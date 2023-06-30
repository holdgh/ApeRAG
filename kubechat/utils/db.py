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


def new_db_client(config):
    # only import class when it is needed
    match config["db_type"]:
        case "mysql" | "postgresql" | "sqlite" | "oracle":
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
            new_client = None
    if new_client is None:
        return None

    client = new_client(
        host=config["host"],
        user=config["username"] if "username" in config.keys() else None,
        pwd=config["password"] if "password" in config.keys() else None,
        port=int(config["port"]) if "port" in config.keys() and config["port"] is not None else None,
        db_type=config["db_type"],
    )
    return client
