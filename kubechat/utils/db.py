import os
from kubechat.models import Collection, CollectionStatus, Document, DocumentStatus, Chat, ChatStatus, \
    ssl_temp_file_path, SslFile
from django.core.files.base import ContentFile


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
    return Chat.objects.exclude(status=DocumentStatus.DELETED).filter(user=user, collection_id=collection_id)


def add_ssl_file(config, user, collection):
    for ssl_file_name in ["ca_cert", "client_key", "client_cert"]:
        if ssl_file_name in config.keys():
            with open(ssl_temp_file_path(config[ssl_file_name]), "rb+") as f:
                name = ssl_file_name + os.path.splitext(f.name)[1]
                ssl_file_instance = SslFile(
                    user=user,
                    name=name,
                    collection=collection,
                    file=ContentFile(f.read(), name),
                )
                ssl_file_instance.save()
