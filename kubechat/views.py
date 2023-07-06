import json
import logging
import os
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import List, Optional

from django.core.files.base import ContentFile
from django.http import HttpResponse
from langchain.memory import RedisChatMessageHistory
from ninja import File, NinjaAPI, Schema
from ninja.files import UploadedFile
from pydantic import BaseModel

import config.settings as settings
from config.vector_db import get_vector_db_connector
from kubechat.tasks.index import add_index_for_document, remove_index
from kubechat.tasks.scan import scan_collection
from kubechat.utils.db import *
from kubechat.utils.request import fail, get_user, success
from readers.base_embedding import get_default_embedding_model

from .auth.validator import GlobalAuth
from .models import *
from .source.ftp import scanning_ftp_add_index
from .utils.utils import generate_vector_db_collection_id

logger = logging.getLogger(__name__)

api = NinjaAPI(version="1.0.0", auth=GlobalAuth())


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


class CodeChatIn(Schema):
    title: str = ""


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


@api.post("/collections")
def create_collection(request, collection: CollectionIn):
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
    instance.save()

    config = json.loads(collection.config)
    if instance.type == CollectionType.DATABASE:
        if config["verify"] != VerifyWay.PREFERRED:
            add_ssl_file(config, instance)
            collection.config = json.dumps(config)
            instance.save()
    elif instance.type == CollectionType.DOCUMENT:
        # pre-create collection in vector db
        vector_db_conn = get_vector_db_connector(
            collection=generate_vector_db_collection_id(user=user, collection=instance.id)
        )
        _, size = get_default_embedding_model(load=False)
        vector_db_conn.connector.create_collection(vector_size=size)
        scan_collection.delay(instance.id)
    return success(instance.view())


@api.get("/collections")
def list_collections(request):
    user = get_user(request)
    instances = query_collections(user)
    response = []
    for instance in instances:
        response.append(instance.view())
    return success(response)


@api.get("/collections/{collection_id}/database")
def get_database_list(request, collection_id):
    user = get_user(request)
    instance = query_collection(user, collection_id)
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
def get_collection(request, collection_id):
    user = get_user(request)
    instance = query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    return success(instance.view())


@api.put("/collections/{collection_id}")
def update_collection(request, collection_id, collection: CollectionIn):
    user = get_user(request)
    instance = query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance.title = collection.title
    instance.description = collection.description
    instance.save()
    return success(instance.view())


@api.delete("/collections/{collection_id}")
def delete_collection(request, collection_id):
    user = get_user(request)
    instance = query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance.status = CollectionStatus.DELETED
    instance.gmt_deleted = datetime.now()
    instance.save()
    return success(instance.view())


@api.post("/collections/{collection_id}/documents")
def add_document(request, collection_id, file: List[UploadedFile] = File(...)):
    user = get_user(request)
    collection = query_collection(user, collection_id)
    if collection is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    response = []
    for item in file:
        document_instance = Document(
            user=user,
            name=item.name,
            status=DocumentStatus.PENDING,
            size=item.size,
            collection=collection,
            file=ContentFile(item.read(), item.name),
        )
        document_instance.save()
        response.append(document_instance.view())
        add_index_for_document.delay(document_instance.id, document_instance.file.name)
    return success(response)


@api.get("/collections/{collection_id}/documents")
def list_documents(request, collection_id):
    user = get_user(request)
    documents = query_documents(user, collection_id)
    response = []
    for document in documents:
        response.append(document.view())
    return success(response)


@api.put("/collections/{collection_id}/documents/{document_id}")
def update_document(
        request, collection_id, document_id, file: UploadedFile = File(...)
):
    user = get_user(request)
    document = query_document(user, collection_id, document_id)
    if document is None:
        return fail(HTTPStatus.NOT_FOUND, "Document not found")

    data = file.read()
    document.file = data
    document.size = len(data)
    document.status = DocumentStatus.PENDING
    document.save()
    return success(document.view())


@api.delete("/collections/{collection_id}/documents/{document_id}")
def delete_document(request, collection_id, document_id):
    user = get_user(request)
    document = query_document(user, collection_id, document_id)
    if document is None:
        return fail(HTTPStatus.NOT_FOUND, "Document not found")
    remove_index.delay(document.id)
    return success(document.view())


@api.post("/collections/{collection_id}/chats")
def add_chat(request, collection_id):
    user = get_user(request)
    collection_instance = query_collection(user, collection_id)
    if collection_instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance = Chat(
        user=user,
        collection=collection_instance,
    )
    instance.save()
    return success(instance.view())


@api.get("/collections/{collection_id}/chats")
def list_chats(request, collection_id):
    user = get_user(request)
    chats = query_chats(user, collection_id)
    response = []
    for chat in chats:
        response.append(chat.view())
    return success(response)


@api.put("/collections/{collection_id}/chats/{chat_id}")
def update_chat(request, collection_id, chat_id):
    user = get_user(request)
    instance = query_chat(user, collection_id, chat_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Chat not found")
    instance.summary = ""
    instance.save()
    history = RedisChatMessageHistory(chat_id, settings.MEMORY_REDIS_URL)
    history.clear()
    return success(instance.view())


@api.get("/collections/{collection_id}/chats/{chat_id}")
def get_chat(request, collection_id, chat_id):
    user = get_user(request)
    chat = query_chat(user, collection_id, chat_id)
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
    return success(chat.view(messages))


@api.delete("/collections/{collection_id}/chats/{chat_id}")
def delete_chat(request, collection_id, chat_id):
    user = get_user(request)
    chat = query_chat(user, collection_id, chat_id)
    if chat is None:
        return fail(HTTPStatus.NOT_FOUND, "Chat not found")
    chat.status = ChatStatus.DELETED
    chat.gmt_deleted = datetime.now()
    chat.save()
    history = RedisChatMessageHistory(chat_id, settings.MEMORY_REDIS_URL)
    history.clear()
    return success(chat.view())


@api.post("/code/codegenerate")
def create_code_generate_chat(request, codechat: CodeChatIn):
    user = get_user(request)
    instance = CodeChat(
        user=user,
        title=codechat.title,
        status=CodeChatStatus.ACTIVE,
    )
    instance.save()
    return success(instance.view())


@api.get("/code/codegenerate/chats")
def list_code_generate_chats(request):
    user = get_user(request)
    instances = query_code_chats(user)
    response = []
    for instance in instances:
        response.append(instance.view())
    return success(response)


@api.get("/code/codegenerate/chats/{chat_id}")
def get_code_generate_chat(request, chat_id):
    user = get_user(request)
    instance = query_code_chat(user, chat_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "chat not found")
    # chat_id will conflict
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
    return success(instance.view(messages))


@api.delete("/code/codegenerate/chats/{chat_id}")
def delete_code_generate_chat(request, chat_id):
    user = get_user(request)
    instance = query_code_chat(user, chat_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "chat not found")
    instance.status = CodeChatStatus.DELETED
    instance.gmt_deleted = datetime.now()
    instance.save()
    return success(instance.view())


def index(request):
    return HttpResponse("KubeChat")
