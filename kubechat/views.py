import logging
import json
import uuid
import os
import config.settings as settings
from datetime import datetime
from typing import List
from typing import Optional, Dict, Type
from http import HTTPStatus
from django.http import HttpResponse
from ninja import NinjaAPI, Schema, File
from ninja.files import UploadedFile
from kubechat.tasks.index import add_index_for_document, remove_index
from kubechat.utils.db import query_collection, query_collections, query_document, query_documents, query_chat, \
    query_chats
from kubechat.utils.request import get_user, success, fail
from langchain.memory import RedisChatMessageHistory
from .models import Collection, CollectionStatus, \
    Document, DocumentStatus, Chat, ChatStatus, \
    VerifyWay, ssl_temp_file_path, CollectionType
from django.core.files.base import ContentFile
from .auth.validator import GlobalAuth


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


@api.post("/collections/ca/upload")
def ssl_file_upload(request, file: UploadedFile = File(...)):
    file_name = uuid.uuid4().hex
    _, file_extension = os.path.splitext(file.name)
    print(file_extension)
    if file_extension not in [".pem", ".key", ".crt", ".csr"]:
        return fail(HTTPStatus.NOT_FOUND, "file extension not found")

    if not os.path.exists(ssl_temp_file_path("")):
        os.makedirs(ssl_temp_file_path(""))

    with open(ssl_temp_file_path(file_name+file_extension), "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    return success(file_name+file_extension)


@api.post("/collections/test_connection")
def connection_test(request, connection: ConnectionInfo):
    verify = (connection.verify != VerifyWay.PREFERRED)
    host = connection.host
    db_type = connection.db_type

    # only import class when it is needed
    match db_type:
        case "mysql", "postgresql", "sqlite", "oracle":
            from services.text2SQL.sql.sql import SQLBase
            new_client = SQLBase
        case "redis":
            from services.text2SQL.nosql import redis_query
            new_client = redis_query.Redis
        case "mongo":
            from services.text2SQL.nosql import mongo_query
            new_client = mongo_query.Mongo
        case "clickhouse":
            from services.text2SQL.nosql import clickhouse_query
            new_client = clickhouse_query.Clickhouse
        case "elasticsearch":
            from services.text2SQL.nosql import elasticsearch_query
            new_client = elasticsearch_query.ElasticsearchClient
        case _:
            return fail(HTTPStatus.NOT_FOUND, "db type not found or illegal")

    if host == "":
        return fail(HTTPStatus.NOT_FOUND, "host not found")

    client = new_client(
        host=host,
        user=connection.username,
        pwd=connection.password,
        port=connection.port,
        db_type=connection.db_type,
    )

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

    if instance.type == CollectionType.DATABASE:
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
    add_index_for_document.delay(document_instance.id)
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
    remove_index.delay(document_id)
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
