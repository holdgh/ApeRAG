from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from ninja import Router
from ninja import NinjaAPI

api = NinjaAPI(version="1.0.0")

@api.post("/collections")
def create_collection(request):
    return {}

@api.get("/collections")
def list_collections(request):
    return {}

@api.put("/collections/{collection_id}")
def update_collection(request, collection_id):
    return {}

@api.delete("/collections/{collection_id}")
def delete_collection(request, collection_id):
    return {}

@api.post("/collections/{collection_id}/documents")
def add_document(request, collection_id):
    return {}

@api.get("/collections/{collection_id}/documents")
def list_documents(request, collection_id):
    return {}

@api.put("/collections/{collection_id}/documents/{document_id}")
def update_document(request, collection_id, document_id):
    return {}

@api.delete("/collections/{collection_id}/documents/{document_id}")
def delete_document(request, collection_id, document_id):
    return {}

@api.post("/collections/{collection_id}/chats")
def add_chat(request, collection_id):
    return {}

@api.get("/collections/{collection_id}/chats")
def list_chats(request, collection_id):
    return {}

@api.delete("/collections/{collection_id}/chats/{chat_id}")
def delete_chat(request, collection_id, chat_id):
    return {}

def index(request):
    return HttpResponse("KubeChat")
