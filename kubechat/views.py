from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from ninja import Router
from ninja import NinjaAPI

api = NinjaAPI()

@api.put("/collections")
def create_collection(request):
    return {}

@api.get("/collections")
def list_collections(request):
    return {}

@api.post("/collections/{collection_id}")
def update_collection(request):
    return {}

@api.delete("/collections/{collection_id}")
def delete_collection(request):
    return {}

@api.put("/collections/{collection_id}/documents")
def add_document(request):
    return {}

@api.get("/collections/{collection_id}/documents")
def list_documents(request):
    return {}

@api.post("/collections/{collection_id}/documents/{document_id}")
def update_document(request):
    return {}

@api.delete("/collections/{collection_id}/documents/{collection_id}")
def delete_document(request):
    return {}

@api.put("/collections/{collection_id}/chats")
def add_chat(request):
    return {}

@api.get("/collections/{collection_id}/chats")
def list_chats(request):
    return {}

@api.delete("/collections/{collection_id}/chats/{chat_id}")
def delete_chat(request):
    return {}

def index(request):
    return HttpResponse("KubeChat")
