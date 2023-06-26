from typing import List
from http import HTTPStatus
from django.http import HttpResponse
from ninja import NinjaAPI, Schema, File
from ninja.security import HttpBearer
from ninja.files import UploadedFile
from .models import Collection, CollectionStatus, \
    Document, DocumentStatus, Chat
from django.core.files.base import ContentFile
from config.settings import AUTH_ENABLED


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        if token == "supersecret":
            return token


api = NinjaAPI(version="1.0.0", auth=GlobalAuth() if AUTH_ENABLED else None)


class CollectionIn(Schema):
    title: str
    type: str
    description: str


class DocumentIn(Schema):
    name: str
    type: str


def get_user_from_token(request):
    # TODO parse user from auth0 token
    return None if getattr(request, "auth", None) is None else request.auth


def query_collection(user, collection_id: str):
    return Collection.objects.exclude(status=CollectionStatus.DELETED).get(user=user, pk=collection_id)


def query_collections(user):
    return Collection.objects.exclude(status=CollectionStatus.DELETED).filter(user=user)


def query_document(user, collection_id: str, document_id: str):
    return Document.objects.exclude(status=DocumentStatus.DELETED).get(user=user, collection_id=collection_id,
                                                                       pk=document_id)


def query_documents(user, collection_id: str):
    return Document.objects.exclude(status=DocumentStatus.DELETED).filter(user=user, collection_id=collection_id)


def query_chat(user, collection_id: str, chat_id: str):
    return Chat.objects.exclude(status=DocumentStatus.DELETED).get(user=user, collection_id=collection_id, pk=chat_id)


def query_chats(user, collection_id: str):
    return Chat.objects.exclude(status=DocumentStatus.DELETED).get(user=user, collection_id=collection_id)


def success(data):
    return {
        "code": HTTPStatus.OK,
        "data": data,
    }


def fail(code, message):
    return {
        "code": code,
        "message": message,
    }


@api.post("/collections")
def create_collection(request, collection: CollectionIn):
    user = get_user_from_token(request)
    instance = Collection(
        title=collection.title,
        description=collection.description,
        type=collection.type,
        status=CollectionStatus.INACTIVE,
    )
    if user is not None:
        instance.user = user
    instance.save()
    return success({"id": instance.id})


@api.get("/collections")
def list_collections(request):
    user = get_user_from_token(request)
    instances = query_collections(user)
    response = []
    for instance in instances:
        response.append(
            {
                "id": instance.id,
                "title": instance.title,
                "description": instance.description,
                "type": instance.type,
                "status": instance.status,
                "created": instance.gmt_created.isoformat(),
                "updated": instance.gmt_updated.isoformat(),
            }
        )
    return success(response)


@api.get("/collections/{collection_id}")
def get_collection(request, collection_id):
    user = get_user_from_token(request)
    instance = query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    response = {
        "id": instance.id,
        "title": instance.title,
        "description": instance.description,
        "type": instance.type,
        "status": instance.status,
        "created": instance.gmt_created.isoformat(),
        "updated": instance.gmt_updated.isoformat(),
    }
    return success(response)


@api.put("/collections/{collection_id}")
def update_collection(request, collection_id, collection: CollectionIn):
    user = get_user_from_token(request)
    instance = query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance.title = collection.title
    instance.description = collection.description
    instance.save()
    return success({"id": collection_id})


@api.delete("/collections/{collection_id}")
def delete_collection(request, collection_id):
    user = get_user_from_token(request)
    instance = query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance.status = CollectionStatus.DELETED
    instance.save()
    return success({"id": collection_id})


@api.post("/collections/{collection_id}/documents")
def add_document(request, collection_id, files: List[UploadedFile] = File(...)):
    user = get_user_from_token(request)
    collection_instance = query_collection(user, collection_id)
    if collection_instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    response = []
    for file in files:
        data = file.read()
        size = len(data)
        document_instance = Document(
            size=size,
            collection=collection_instance,
            file=ContentFile(data, file.name),
            status=DocumentStatus.RUNNING,
        )
        document_instance.save()
        response.append(
            {
                "id": document_instance.id,
            }
        )
    return success(response)


@api.get("/collections/{collection_id}/documents")
def list_documents(request, collection_id):
    user = get_user_from_token(request)
    collection_instance = query_collection(user, collection_id)
    if collection_instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    documents = query_documents(user, collection_id)
    response = []
    for document in documents:
        response.append(
            {
                "id": document.id,
                "name": document.name,
                "status": document.status,
                "created": document.gmt_created.isoformat(),
                "updated": document.gmt_updated.isoformat(),
            }
        )
    return success(response)


@api.put("/collections/{collection_id}/documents/{document_id}")
def update_document(request, collection_id, document_id, file: UploadedFile = File(...)):
    user = get_user_from_token(request)
    collection_instance = query_collection(user, collection_id)
    if collection_instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    document = query_document(user, collection_id, document_id)
    if document is None:
        return fail(HTTPStatus.NOT_FOUND, "Document not found")

    data = file.read()
    document.file = data
    document.size = len(data)
    document.save()

    return success({"id": document_id})


@api.delete("/collections/{collection_id}/documents/{document_id}")
def delete_document(request, collection_id, document_id):
    user = get_user_from_token(request)
    collection_instance = query_collection(user, collection_id)
    if collection_instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    document = query_document(user, collection_id, document_id)
    if document is None:
        return fail(HTTPStatus.NOT_FOUND, "Document not found")
    document.status = DocumentStatus.DELETED
    document.save()
    return success({"id": document_id})


@api.post("/collections/{collection_id}/chats")
def add_chat(request, collection_id):
    return {}


@api.get("/collections/{collection_id}/chats")
def list_chats(request, collection_id):
    return {}


@api.get("/collections/{collection_id}/chats/{chat_id}")
def get_chat(request, collection_id, chat_id):
    return {}


@api.delete("/collections/{collection_id}/chats/{chat_id}")
def delete_chat(request, collection_id, chat_id):
    return {}


@api.get("/bearer")
def bearer(request):
    return {"token": request.auth}


def index(request):
    return HttpResponse("KubeChat")
