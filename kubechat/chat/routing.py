from asgiref.sync import sync_to_async
from django.urls import re_path

from kubechat.utils.utils import extract_collection_and_chat_id


async def collection_consumer_router(scope, receive, send):
    from kubechat.models import CollectionType
    from kubechat.utils.db import query_chat, query_collection

    user = scope["X-USER-ID"]
    path = scope["path"]
    collection_id, chat_id = extract_collection_and_chat_id(path)
    collection = await query_collection(user, collection_id)
    if collection is None:
        raise Exception("Collection not found")

    chat = await query_chat(user, collection_id, chat_id)
    if chat is None:
        raise Exception("Chat not found")

    if collection.type == CollectionType.DOCUMENT:
        from .document_qa_consumer import DocumentQAConsumer
        from .mock_consumer import MockConsumer

        return await MockConsumer.as_asgi()(scope, receive, send)
    elif collection.type == CollectionType.DATABASE:
        from .text_2_sql_consumer import Text2SQLConsumer

        return await Text2SQLConsumer.as_asgi()(scope, receive, send)
    elif collection.type == CollectionType.CODE:
        from kubechat.chat.code_generate_consumer import CodeGenerateConsumer
        return await CodeGenerateConsumer.as_asgi()(scope, receive, send)
    else:
        raise Exception("Invalid collection type")


async def chat_bot_consumer_router(scope, receive, send):
    from .chat_bot_consumer import ChatBotConsumer

    return await ChatBotConsumer.as_asgi()(scope, receive, send)


async def code_generate_chat_consumer_router(scope, receive, send):
    # for .code_generate_con
    from .code_generate_consumer import CodeGenerateConsumer
    return await CodeGenerateConsumer.as_asgi()(scope, receive, send)


websocket_urlpatterns = [
    re_path(
        r"api/v1/collections/(?P<collection_id>\w+)/chats/(?P<chat_id>\w+)/connect$",
        collection_consumer_router,
    ),
    re_path(
        r"api/v1/bot/(?P<chat_id>\w+)/connect$",
        chat_bot_consumer_router,
    ),
    # re_path(r"api/v1/code/(?P<chat_id>\w+)/connect$", code_generate_chat_consumer_router)
]
