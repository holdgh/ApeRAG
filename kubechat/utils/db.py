import os
import shutil
from typing import Any, Dict, Optional

from django.db.models import QuerySet
from pydantic import BaseModel

from kubechat.models import (
    Bot,
    Chat,
    ChatStatus,
    Collection,
    CollectionStatus,
    CollectionSyncHistory,
    Document,
    DocumentStatus,
    ssl_file_path,
    ssl_temp_file_path, BotStatus, MessageFeedback, CollectionSyncStatus,
)


class PagedQuery(BaseModel):
    page_number: Optional[int]
    page_size: Optional[int]
    match_key: Optional[str]
    match_value: Optional[str]
    order_by: Optional[str]
    order_desc: Optional[bool]


class PagedResult(BaseModel):
    count: int
    page_number: int = 1
    page_size: int = 10
    data: Any


def build_pq(request) -> Optional[PagedQuery]:
    # FIXME this is compatible with the old frontend, once the frontend is updated,
    # FIXME we should do pagination and add default page_number and page_size
    page_number = request.GET.get('page_number')
    page_size = request.GET.get('page_size')
    if not page_number or not page_size:
        return None

    match_key = request.GET.get('match_key', "")
    match_value = request.GET.get('match_value', "")
    order_by = request.GET.get('order_by', "")
    order_desc = request.GET.get('order_desc', "true")
    return PagedQuery(
        page_number=int(page_number),
        page_size=int(page_size),
        match_key=match_key,
        match_value=match_value,
        order_by=order_by,
        order_desc=order_desc.lower() == "true",
    )


def build_order_by(pq: PagedQuery) -> str:
    if not pq or not pq.order_by:
        return "gmt_created"
    return f"{'' if pq.order_desc else '-'}{pq.order_by}"


async def build_pr(pq: PagedQuery, query_set: QuerySet) -> PagedResult:
    if not pq:
        return PagedResult(count=-1, data=query_set)

    offset = (pq.page_number - 1) * pq.page_size
    limit = pq.page_size
    count = await get_count(query_set)
    query_set = query_set.order_by(build_order_by(pq))
    return PagedResult(count=count, page_number=pq.page_number, page_size=pq.page_size,
                       data=query_set[offset:offset + limit])


def build_filters(pq: PagedQuery) -> Dict:
    if not pq:
        return {}
    if not pq.match_key or not pq.match_value:
        return {}
    return {
        f"{pq.match_key}__icontains": pq.match_value
    }


async def get_count(collection) -> int:
    return await collection.acount()


async def query_collection(user, collection_id: str):
    try:
        return await Collection.objects.exclude(status=CollectionStatus.DELETED).aget(
            user=user, pk=collection_id
        )
    except Collection.DoesNotExist:
        return None


async def query_collections(user, pq: PagedQuery = None):
    filters = build_filters(pq)
    query_set = Collection.objects.exclude(status=CollectionStatus.DELETED).filter(user=user, **filters)
    return await build_pr(pq, query_set)


async def query_document(user, collection_id: str, document_id: str):
    try:
        return await Document.objects.exclude(status=DocumentStatus.DELETED).aget(
            user=user, collection_id=collection_id, pk=document_id
        )
    except Document.DoesNotExist:
        return None


async def query_documents(user, collection_id: str, pq: PagedQuery = None):
    filters = build_filters(pq)
    query_set = Document.objects.exclude(status=DocumentStatus.DELETED).filter(
        user=user, collection_id=collection_id, **filters)
    return await build_pr(pq, query_set)


async def query_chat(user, bot_id: str, chat_id: str):
    try:
        return await Chat.objects.exclude(status=ChatStatus.DELETED).aget(
            user=user, bot_id=bot_id, pk=chat_id)
    except Chat.DoesNotExist:
        return None


async def query_chat_feedbacks(user, chat_id: str, pq: PagedQuery = None):
    filters = build_filters(pq)
    query_set = MessageFeedback.objects.filter(user=user, chat_id=chat_id, **filters)
    return await build_pr(pq, query_set)


async def query_message_feedback(user, bot_id: str, chat_id: str, message_id: str):
    try:
        return await MessageFeedback.objects.exclude.aget(
            user=user, bot_id=bot_id, chat_id=chat_id, message_id=message_id)
    except MessageFeedback.DoesNotExist:
        return None


async def query_chat_by_peer(user, peer_type, peer_id: str):
    try:
        return await Chat.objects.exclude(status=ChatStatus.DELETED).aget(
            user=user, peer_type=peer_type, peer_id=peer_id)
    except Chat.DoesNotExist:
        return None


async def query_sync_history(user, collection_id: str, sync_history_id: str):
    try:
        return await CollectionSyncHistory.objects.aget(
            user=user, collection_id=collection_id, pk=sync_history_id
        )
    except CollectionSyncHistory.DoesNotExist:
        return None


async def query_sync_histories(user, collection_id: str, pq: PagedQuery = None):
    filters = build_filters(pq)
    query_set = CollectionSyncHistory.objects.filter(user=user, collection_id=collection_id, **filters)
    return await build_pr(pq, query_set)


async def query_chats(user, bot_id: str, pq: PagedQuery = None):
    filters = build_filters(pq)
    query_set = Chat.objects.exclude(status=ChatStatus.DELETED).filter(user=user, bot_id=bot_id, **filters)
    return await build_pr(pq, query_set)


async def query_running_sync_histories(user, collection_id: str, pq: PagedQuery = None):
    filters = build_filters(pq)
    query_set = CollectionSyncHistory.objects.filter(
        user=user, collection_id=collection_id, status=CollectionSyncStatus.RUNNING, **filters,
    ).order_by('-id')
    return await build_pr(pq, query_set)


async def query_bot(user, bot_id: str):
    try:
        return await Bot.objects.exclude(status=BotStatus.DELETED).aget(user=user, pk=bot_id)
    except Bot.DoesNotExist:
        return None


async def query_bots(user, pq: PagedQuery = None):
    filters = build_filters(pq)
    query_set = Bot.objects.exclude(status=BotStatus.DELETED).filter(user=user, **filters)
    return await build_pr(pq, query_set)


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
