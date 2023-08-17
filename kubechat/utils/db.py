import os
import shutil

from django.core.files.base import ContentFile

from kubechat.models import (
    Chat,
    ChatStatus,
    Collection,
    CollectionStatus,
    CollectionSyncHistory,
    Document,
    DocumentStatus,
    ssl_file_path,
    ssl_temp_file_path,
)


async def query_collection(user, collection_id: str):
    return await Collection.objects.exclude(status=CollectionStatus.DELETED).aget(
        user=user, pk=collection_id
    )


async def query_collections(user):
    return Collection.objects.exclude(status=CollectionStatus.DELETED).filter(user=user)


async def query_document(user, collection_id: str, document_id: str):
    return await Document.objects.exclude(status=DocumentStatus.DELETED).aget(
        user=user, collection_id=collection_id, pk=document_id
    )


async def query_documents(user, collection_id: str):
    return Document.objects.exclude(status=DocumentStatus.DELETED).filter(
        user=user, collection_id=collection_id
    )


async def query_sync_history(user, collection_id: str, sync_history_id: str):
    return CollectionSyncHistory.objects.aget(
        user=user, collection_id=collection_id, pk=sync_history_id
    )


async def query_sync_histories(user, collection_id: str):
    return CollectionSyncHistory.objects.filter(
        user=user, collection_id=collection_id
    )


async def query_chat(user, collection_id: str, chat_id: str):
    return await Chat.objects.exclude(status=DocumentStatus.DELETED).aget(
        user=user, collection_id=collection_id, pk=chat_id
    )


async def query_chats(user, collection_id: str):
    return Chat.objects.exclude(status=DocumentStatus.DELETED).filter(
        user=user, collection_id=collection_id
    )


def add_ssl_file(config, collection):
    if not os.path.exists(ssl_file_path(collection, "")):
        os.makedirs(ssl_file_path(collection, ""))

    for ssl_file_type in ["ca_cert", "client_key", "client_cert"]:
        if ssl_file_type in config.keys():
            ssl_temp_name = config[ssl_file_type]
            _, file_extension = os.path.splitext(ssl_temp_name)
            ssl_file_name = ssl_file_type + file_extension
            whole_ssl_file_path = ssl_file_path(collection, ssl_file_name)
            shutil.move(ssl_temp_file_path(ssl_temp_name), whole_ssl_file_path)
            config[ssl_file_type] = whole_ssl_file_path


def new_db_client(config):
    # only import class when it is needed
    match config["db_type"]:
        case "sqlite" | "oracle":
            from services.text2SQL.sql.sql import SQLBase

            new_client = SQLBase
        case "postgresql":
            from services.text2SQL.sql.postgresql import Postgresql

            new_client = Postgresql
        case "mysql":
            from services.text2SQL.sql.mysql import Mysql

            new_client = Mysql
        case "redis":
            from services.text2SQL.nosql.redis_query import Redis

            new_client = Redis
        case "mongo":
            from services.text2SQL.nosql.mongo_query import Mongo

            new_client = Mongo
        case "clickhouse":
            from services.text2SQL.nosql.clickhouse_query import Clickhouse

            new_client = Clickhouse
        case "elasticsearch":
            from services.text2SQL.nosql.elasticsearch_query import ElasticsearchClient

            new_client = ElasticsearchClient
        case _:
            new_client = None
    if new_client is None:
        return None

    client = new_client(
        host=config["host"],
        user=config["username"] if "username" in config.keys() else None,
        pwd=config["password"] if "password" in config.keys() else None,
        port=int(config["port"])
        if "port" in config.keys() and config["port"] is not None
        else None,
        db_type=config["db_type"],
        db=config["db_name"] if "db_name" in config.keys() else "",
    )
    return client
