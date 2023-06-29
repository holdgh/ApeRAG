from django.urls import re_path
from kubechat.utils.utils import extract_collection_and_chat_id
from asgiref.sync import sync_to_async

from .document_qa_consumer import DocumentSizeConsumer, DocumentQAConsumer
from .text_2_sql_consumer import Text2SQLConsumer
from .chat_bot_consumer import ChatBotConsumer


async def collection_consumer_router(scope, receive, send):
    from kubechat.utils.db import query_collection, query_chat
    from kubechat.models import CollectionType
    user = scope["X-USER-ID"]
    path = scope["path"]
    collection_id, chat_id = extract_collection_and_chat_id(path)
    collection = await sync_to_async(query_collection)(user, collection_id)
    if collection is None:
        raise Exception("Collection not found")

    chat = await sync_to_async(query_chat)(user, collection_id, chat_id)
    if chat is None:
        raise Exception("Chat not found")

    if collection.type == CollectionType.DOCUMENT:
        return await DocumentQAConsumer.as_asgi()(scope, receive, send)
    elif collection.type == CollectionType.DATABASE:
        return await Text2SQLConsumer.as_asgi()(scope, receive, send)
    else:
        raise Exception("Invalid collection type")


async def chat_bot_consumer_router(scope, receive, send):
    return await ChatBotConsumer.as_asgi()(scope, receive, send)


websocket_urlpatterns = [
    re_path(
        r"api/v1/collections/(?P<collection_id>\w+)/chats/(?P<chat_id>\w+)/connect$", collection_consumer_router,
    ),
    re_path(
        r"api/v1/bot/(?P<chat_id>\w+)/connect$", chat_bot_consumer_router,
    )
]
