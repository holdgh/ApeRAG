import json
import config.settings as settings
from datetime import datetime
from typing import List
from typing import Optional
from http import HTTPStatus
from django.http import HttpResponse
from ninja import NinjaAPI, Schema, File
from ninja.files import UploadedFile
from kubechat.tasks.add_index import add_index_for_document
from kubechat.auth.validator import GlobalAuth
from kubechat.utils.db import query_collection, query_collections, query_document, query_documents, query_chat, query_chats
from kubechat.utils.request import get_user, success, fail
from langchain.memory import RedisChatMessageHistory
from .models import Collection, CollectionStatus, \
    Document, DocumentStatus, Chat, ChatStatus, \
    VerifyWay, DatabaseTypes
from django.core.files.base import ContentFile
from .auth.validator import GlobalAuth
from services.text2SQL.nosql import redis_query, mongo_query, clickhouse_query, elasticsearch_query


api = NinjaAPI(version="1.0.0", auth=GlobalAuth() if settings.AUTH_ENABLED else None)


class CollectionIn(Schema):
    title: str
    type: str
    description: Optional[str]
    config: Optional[str]


class DocumentIn(Schema):
    name: str
    type: str


class ChatIn(Schema):
    history: Optional[str]


class ConnectionInfo(Schema):
    db_type: DatabaseTypes
    host: str
    port: Optional[str]
    db_name: Optional[str]
    username: Optional[str]
    password: Optional[str]
    verify: VerifyWay
    ca_cert: Optional[str]
    client_key: Optional[str]
    client_cert: Optional[str]


def new_client(db_type, host, port):
    if db_type == DatabaseTypes.REDIS:
        return redis_query.Redis(host=host, port=port)
    elif db_type == DatabaseTypes.MONGO:
        # TODO:mongo collections
        return mongo_query.Mongo(host=host, port=port, collection="")
    elif db_type == DatabaseTypes.CLICKHOUSE:
        return clickhouse_query.Clickhouse(host=host, port=port)
    elif db_type == DatabaseTypes.ELASTICSEARCH:
        return elasticsearch_query.ElasticsearchClient(host=host, port=port)
    else:
        # TODO:new sql Database
        return


@api.get("/collections/test_connection")
def test_connection(request, connection: ConnectionInfo):
    verify = (connection.verify != VerifyWay.PREFERRED)
    host = connection.host
    db_type = connection.db_type

    if db_type == "" or db_type not in DatabaseTypes:
        return fail(HTTPStatus.NOT_FOUND, "db type not found or illegal")
    if host == "":
        return fail(HTTPStatus.NOT_FOUND, "host not found")

    client = new_client(db_type, host, connection.port)

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
        status=CollectionStatus.INACTIVE,
        title=collection.title,
        description=collection.description,
    )
    if collection.config is not None:
        instance.config = collection.config
    instance.save()
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
    document.status = DocumentStatus.DELETED
    document.gmt_deleted = datetime.now()
    document.save()
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
def update_chat(request, collection_id, chat_id, chat: ChatIn):
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
        item = json.loads(message.content)
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
