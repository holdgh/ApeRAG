import io
import json
import logging
import uuid
import zipfile
from pathlib import Path
from datetime import datetime
from http import HTTPStatus

from typing import List, Optional, Any
from kubechat.source.base import Source, get_source
from asgiref.sync import sync_to_async
from django.http import HttpResponse
from django_celery_beat.models import PeriodicTask
from fsspec.asyn import loop
from langchain.memory import RedisChatMessageHistory
from ninja import File, NinjaAPI, Schema
from ninja.files import UploadedFile
from pydantic import BaseModel
from kubechat.tasks.code_generate import pre_clarify  # can't remove or pre_clarify task will be NotRegister
import config.settings as settings
from config.vector_db import get_vector_db_connector
from kubechat.tasks.index import add_index_for_local_document, remove_index
from kubechat.tasks.scan import scan_collection, sync_documents_cron_job, delete_sync_documents_cron_job, \
    update_sync_documents_cron_job
from kubechat.utils.db import *
from kubechat.utils.request import fail, get_user, success
from readers.Readers import DEFAULT_FILE_READER_CLS
from kubechat.tasks.sync_documents_task import sync_documents
from config.celery import app
from celery.schedules import crontab

from readers.base_embedding import get_default_embedding_model

from .auth.validator import GlobalHTTPAuth
from .chat.prompts import DEFAULT_MODEL_PROMPT_TEMPLATES, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2
from .models import *
from .utils.utils import generate_vector_db_collection_id, fix_path_name, validate_document_config

from django.contrib.auth.models import User
from django.shortcuts import render

logger = logging.getLogger(__name__)

api = NinjaAPI(version="1.0.0", auth=GlobalHTTPAuth(), urls_namespace="collection")


class CollectionIn(Schema):
    title: str
    type: str
    description: Optional[str]
    config: Optional[str]


class DocumentIn(Schema):
    name: str
    type: str


class ConnectionInfo(Schema):
    db_type: str
    host: str
    port: Optional[int]
    db_name: Optional[str]
    username: Optional[str]
    password: Optional[str]
    verify: VerifyWay
    ca_cert: Optional[str]
    client_key: Optional[str]
    client_cert: Optional[str]


class Auth(BaseModel):
    username: str = ""
    password: str = ""


class Host(BaseModel):
    source: str = "system"
    host: str = ""
    port: str = ""


class DocumentConfig(BaseModel):
    host: Host = Host
    auth: Auth = Auth
    filedir: str = ""
    filepath: str = ""


@api.post("/collections/ca/upload")
def ssl_file_upload(request, file: UploadedFile = File(...)):
    file_name = uuid.uuid4().hex
    _, file_extension = os.path.splitext(file.name)
    print(file_extension)
    if file_extension not in [".pem", ".key", ".crt", ".csr"]:
        return fail(HTTPStatus.NOT_FOUND, "file extension not found")

    if not os.path.exists(ssl_temp_file_path("")):
        os.makedirs(ssl_temp_file_path(""))

    with open(ssl_temp_file_path(file_name + file_extension), "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    return success(file_name + file_extension)


@api.post("/collections/test_connection")
def connection_test(request, connection: ConnectionInfo):
    verify = connection.verify != VerifyWay.PREFERRED
    host = connection.host

    if host == "":
        return fail(HTTPStatus.NOT_FOUND, "host not found")

    client = new_db_client(dict(connection))
    if client is None:
        return fail(HTTPStatus.NOT_FOUND, "db type not found or illegal")

    if not client.connect(
            False,
            ssl_temp_file_path(connection.ca_cert),
            ssl_temp_file_path(connection.client_key),
            ssl_temp_file_path(connection.client_cert),
    ):
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, "can not connect")

    return success("successfully connected")


@api.get("/collections/models")
def list_model_name(request):
    response = []
    model_servers = json.loads(settings.MODEL_SERVERS)
    if model_servers is None:
        return fail(HTTPStatus.NOT_FOUND, "model name not found")
    for model_server in model_servers:
        response.append({
            "value": model_server["name"],
            "label": model_server.get("label", model_server["name"]),
            "enabled": model_server.get("enabled", "true").lower() == "true",
            "prompt_template": DEFAULT_MODEL_PROMPT_TEMPLATES.get(model_server["name"],
                                                                  DEFAULT_CHINESE_PROMPT_TEMPLATE_V2),
            "context_window": model_server.get("context_window", 2000),
        })
    return success(response)


@api.post("/collections/{collection_id}/sync")
def sync_immediately(request, collection_id):
    user = get_user(request)
    result = sync_documents.delay(collection_id=collection_id)
    sync_history_id = result.get(timeout=300)
    if sync_history_id == -1:
        return fail(HTTPStatus.BAD_REQUEST, "source type not supports sync")
    sync_history = CollectionSyncHistory.objects.get(id=sync_history_id)
    return success(sync_history.view())


@api.get("/collections/{collection_id}/sync/history")
async def get_sync_histories(request, collection_id):
    user = get_user(request)
    sync_histories = await query_sync_histories(user, collection_id)
    response = []
    async for sync_history in sync_histories:
        response.append(sync_history.view())
    return success(response)


@api.get("/collections/{collection_id}/sync/{sync_history_id}")
async def get_sync_history(request, collection_id, sync_history_id):
    user = get_user(request)
    sync_history = await query_sync_history(user, collection_id, sync_history_id)
    return success(sync_history.view())


@api.post("/collections")
async def create_collection(request, collection: CollectionIn):
    user = get_user(request)
    instance = Collection(
        user=user,
        type=collection.type,
        status=CollectionStatus.ACTIVE,
        title=collection.title,
        description=collection.description,
    )

    if collection.config is not None:
        instance.config = collection.config
    await instance.asave()

    config = json.loads(collection.config)
    if instance.type == CollectionType.DATABASE:
        if config["verify"] != VerifyWay.PREFERRED:
            add_ssl_file(config, instance)
            collection.config = json.dumps(config)
            await instance.asave()
    elif instance.type == CollectionType.DOCUMENT:
        # pre-create collection in vector db
        if not validate_document_config(config):
            return fail(HTTPStatus.BAD_REQUEST, "config invalidate")
        vector_db_conn = get_vector_db_connector(
            collection=generate_vector_db_collection_id(user=user, collection=instance.id)
        )
        _, size = get_default_embedding_model(load=False)
        vector_db_conn.connector.create_collection(vector_size=size)
        scan_collection.delay(instance.id)
        # create a period_task to sync documents
        source = get_source(collection, json.loads(collection.config))
        if source.sync_enabled():
            sync_documents_cron_job.delay(instance.id)

    elif instance.type == CollectionType.CODE:
        chat = Chat(
            user=instance.user,
            status=ChatStatus.ACTIVE,
            collection=instance,
            summary=instance.description,
        )
        await chat.asave()
    else:
        return fail(HTTPStatus.BAD_REQUEST, "unknown collection type")

    return success(instance.view())


@api.get("/collections")
async def list_collections(request):
    user = get_user(request)
    instances = await query_collections(user)
    response = []
    async for instance in instances:
        response.append(instance.view())
    return success(response)


@api.get("/collections/{collection_id}/database")
async def get_database_list(request, collection_id):
    user = get_user(request)
    instance = await query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    config = json.loads(instance.config)
    db_type = config["db_type"]
    if db_type not in ["mysql", "postgresql"]:
        return fail(
            HTTPStatus.NOT_FOUND, "{} don't have multiple databases".format(db_type)
        )

    client = new_db_client(config)
    # TODO:add SSL
    if not client.connect(
            False,
    ):
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, "can not connect")

    response = client.get_database_list()
    return success(response)


@api.get("/collections/{collection_id}")
async def get_collection(request, collection_id):
    user = get_user(request)
    instance = await query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    return success(instance.view())


@api.put("/collections/{collection_id}")
async def update_collection(request, collection_id, collection: CollectionIn):
    user = get_user(request)
    instance = await query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance.title = collection.title
    instance.description = collection.description
    instance.config = collection.config
    await instance.asave()
    update_sync_documents_cron_job.delay(instance.id)
    return success(instance.view())


@api.delete("/collections/{collection_id}")
async def delete_collection(request, collection_id):
    user = get_user(request)
    instance = await query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance.status = CollectionStatus.DELETED
    delete_sync_documents_cron_job.delay(instance.id)
    instance.gmt_deleted = timezone.now()
    await instance.asave()
    return success(instance.view())


@api.post("/collections/{collection_id}/documents")
async def add_document(request, collection_id, file: List[UploadedFile] = File(...)):
    user = get_user(request)
    collection = await query_collection(user, collection_id)
    if collection is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    response = []
    for item in file:
        file_suffix = os.path.splitext(item.name)[1].lower()
        if file_suffix in DEFAULT_FILE_READER_CLS.keys():
            document_instance = Document(
                user=user,
                name=item.name,
                status=DocumentStatus.PENDING,
                size=item.size,
                collection=collection,
                file=ContentFile(item.read(), item.name),
            )
            await document_instance.asave()
            response.append(document_instance.view())
            add_index_for_local_document.delay(document_instance.id)
        else:
            logger.error("uploaded a file of unexpected file type.")
    return success(response)


@api.get("/collections/{collection_id}/documents")
async def list_documents(request, collection_id):
    user = get_user(request)
    documents = await query_documents(user, collection_id)
    response = []
    async for document in documents:
        response.append(document.view())
    return success(response)


@api.put("/collections/{collection_id}/documents/{document_id}")
async def update_document(
        request, collection_id, document_id, file: UploadedFile = File(...)
):
    user = get_user(request)
    document = await query_document(user, collection_id, document_id)
    if document is None:
        return fail(HTTPStatus.NOT_FOUND, "Document not found")

    data = file.read()
    document.file = data
    document.size = len(data)
    document.status = DocumentStatus.PENDING
    await document.asave()
    return success(document.view())


@api.delete("/collections/{collection_id}/documents/{document_id}")
async def delete_document(request, collection_id, document_id):
    user = get_user(request)
    document = await query_document(user, collection_id, document_id)
    if document is None:
        return fail(HTTPStatus.NOT_FOUND, "Document not found")
    remove_index.delay(document.id)
    return success(document.view())


@api.post("/collections/{collection_id}/chats")
async def add_chat(request, collection_id):
    user = get_user(request)
    collection_instance = await query_collection(user, collection_id)
    if collection_instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance = Chat(
        user=user,
        collection=collection_instance,
    )
    await instance.asave()
    return success(instance.view(collection_id))


@api.get("/collections/{collection_id}/chats")
async def list_chats(request, collection_id):
    user = get_user(request)
    chats = await query_chats(user, collection_id)
    response = []
    async for chat in chats:
        response.append(chat.view(collection_id))
    return success(response)


@api.put("/collections/{collection_id}/chats/{chat_id}")
async def update_chat(request, collection_id, chat_id):
    user = get_user(request)
    instance = await query_chat(user, collection_id, chat_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Chat not found")
    instance.summary = ""
    await instance.asave()
    history = RedisChatMessageHistory(chat_id, settings.MEMORY_REDIS_URL)
    history.clear()
    return success(instance.view(collection_id))


@api.get("/collections/{collection_id}/chats/{chat_id}")
async def get_chat(request, collection_id, chat_id):
    user = get_user(request)
    chat = await query_chat(user, collection_id, chat_id)
    if chat is None:
        return fail(HTTPStatus.NOT_FOUND, "Chat not found")

    history = RedisChatMessageHistory(chat_id, url=settings.MEMORY_REDIS_URL)
    messages = []
    for message in history.messages:
        try:
            item = json.loads(message.content)
        except Exception as e:
            logger.exception(e)
            continue
        item["role"] = message.additional_kwargs["role"]
        item["references"] = message.additional_kwargs.get("references") or []
        messages.append(item)
    return success(chat.view(collection_id, messages))


@api.delete("/collections/{collection_id}/chats/{chat_id}")
async def delete_chat(request, collection_id, chat_id):
    user = get_user(request)
    chat = await query_chat(user, collection_id, chat_id)
    if chat is None:
        return fail(HTTPStatus.NOT_FOUND, "Chat not found")
    chat.status = ChatStatus.DELETED
    chat.gmt_deleted = datetime.now()
    await chat.asave()
    history = RedisChatMessageHistory(chat_id, settings.MEMORY_REDIS_URL)
    history.clear()
    return success(chat.view())


@api.get("/code/codegenerate/download/{chat_id}")
async def download_code(request, chat_id):
    user = get_user(request)
    chat = await Chat.objects.exclude(status=DocumentStatus.DELETED).aget(
        user=user, pk=chat_id
    )

    @sync_to_async
    def get_collection():
        return chat.collection

    collection = await get_collection()
    if chat.user != user:
        return success("No access to the file")
    if chat.status != ChatStatus.UPLOADED:
        return success("The file is not ready for download")
    base_dir = Path(settings.CODE_STORAGE_DIR)
    buffer = io.BytesIO()
    zip = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    workspace = base_dir / "generated-code" / fix_path_name(user) / fix_path_name(
        collection.title + str(chat_id)) / "workspace"

    for root, dirs, files in os.walk(str(workspace)):
        for file in files:
            zip.write(os.path.join(root, file), arcname=file)
    zip.close()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue())
    response['Content-Disposition'] = f"attachment; filename=\"{collection.title}.zip\""
    response['Content-Type'] = 'application/zip'
    return response


def default_page(request, exception):
    return render(request, '404.html')


def index(request):
    return HttpResponse("KubeChat")


def dashboard(request):
    user_count = User.objects.count()
    collection_count = Collection.objects.count()
    document_count = Document.objects.count()
    chat_count = Chat.objects.count()
    context = {'user_count': user_count, 'Collection_count': collection_count,
               'Document_count': document_count, 'Chat_count': chat_count}
    return render(request, 'kubechat/dashboard.html', context)
