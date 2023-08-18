from asgiref.sync import sync_to_async
from django.urls import re_path

from kubechat.utils.utils import extract_bot_and_chat_id


async def bot_consumer_router(scope, receive, send):
    from kubechat.models import CollectionType
    from kubechat.utils.db import query_chat
    from kubechat.utils.db import query_bot

    user = scope["X-USER-ID"]
    path = scope["path"]
    bot_id, chat_id = extract_bot_and_chat_id(path)
    bot = await query_bot(user, bot_id)
    if bot is None:
        raise Exception("Collection not found")
    collection = await sync_to_async(bot.collections.first)()

    chat = await query_chat(user, bot_id, chat_id)
    if chat is None:
        raise Exception("Chat not found")

    if collection.type == CollectionType.DOCUMENT:
        from .document_qa_consumer import DocumentQAConsumer
        from .mock_consumer import MockConsumer

        return await DocumentQAConsumer.as_asgi()(scope, receive, send)
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
        r"api/v1/bots/(?P<bot_id>\w+)/chats/(?P<chat_id>\w+)/connect$",
        bot_consumer_router,
    ),
    re_path(
        r"api/v1/bot/(?P<chat_id>\w+)/connect$",
        chat_bot_consumer_router,
    ),
    # re_path(r"api/v1/code/(?P<chat_id>\w+)/connect$", code_generate_chat_consumer_router)
]
