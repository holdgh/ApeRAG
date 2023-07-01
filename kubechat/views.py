import logging
import json
import uuid
import os
import config.settings as settings
from datetime import datetime
from typing import List
from typing import Optional
from http import HTTPStatus
from django.http import HttpResponse
from ninja import NinjaAPI, Schema, File
from ninja.files import UploadedFile
from kubechat.tasks.index import add_index_for_document, remove_index
from kubechat.utils.db import query_collection, query_collections, query_document, query_documents, query_chat, \
    query_chats, add_ssl_file, new_db_client
from kubechat.utils.request import get_user, success, fail
from langchain.memory import RedisChatMessageHistory
from .models import Collection, CollectionStatus, \
    Document, DocumentStatus, Chat, ChatStatus, \
    VerifyWay, ssl_temp_file_path, CollectionType
from django.core.files.base import ContentFile
from .auth.validator import GlobalAuth
from pydantic import BaseModel

from .source.ftp import scanning_dir_add_index_from_ftp

logger = logging.getLogger(__name__)

api = NinjaAPI(version="1.0.0", auth=GlobalAuth() if settings.AUTH_ENABLED else None)


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
    source: str = 'system'
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
    verify = (connection.verify != VerifyWay.PREFERRED)
    host = connection.host

    if host == "":
        return fail(HTTPStatus.NOT_FOUND, "host not found")

    client = new_db_client(dict(connection))
    if client is None:
        return fail(HTTPStatus.NOT_FOUND, "db type not found or illegal")

    if not client.connect(
            verify,
            connection.ca_cert,
            connection.client_key,
            connection.client_cert,
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
            add_ssl_file(config, user, instance)
    else:
        if config["source"] == "system":
            pass
        elif config["source"] == "local":
            from kubechat.source.local import scanning_dir_add_index
            scanning_dir_add_index(config["path"], instance)
        elif config["source"] == "s3":
            pass
        elif config["source"] == "oss":
            from kubechat.source.oss import scanning_oss_add_index
            scanning_oss_add_index(config["bucket"], config["access_key_id"], config["secret_access_key"], config["region"], instance)
        elif config["source"] == "ftp":
            scanning_dir_add_index_from_ftp(config["path"], config["host"], config["username"], config["password"],
                                            instance)
        elif config["source"] == "email":
            pass

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
        return fail(HTTPStatus.NOT_FOUND, "{} don't have multiple databases".format(db_type))

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
        add_index_for_document.delay(document_instance)
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
def update_document(request, collection_id, document_id, file: UploadedFile = File(...)):
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
    remove_index.delay(document)
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


def index(request):
    return HttpResponse("KubeChat")
