from asgiref.sync import sync_to_async
from django.urls import re_path

from config import settings
from kubechat.utils.utils import extract_bot_and_chat_id, extract_web_bot_and_chat_id
from kubechat.utils.constant import KEY_USER_ID, KEY_BOT_ID, KEY_CHAT_ID


async def bot_consumer_router(scope, receive, send):
    from kubechat.db.models import CollectionType
    from kubechat.db.ops import query_chat
    from kubechat.db.ops import query_bot

    user = scope.get(KEY_USER_ID, None)
    path = scope["path"]
    bot_id, chat_id = extract_bot_and_chat_id(path)
    bot = await query_bot(user, bot_id)
    if bot is None:
        raise Exception("Bot not found")
    scope[KEY_BOT_ID] = bot_id
    collection = await sync_to_async(bot.collections.first)()

    chat = await query_chat(user, bot_id, chat_id)
    if chat is None:
        raise Exception("Chat not found")
    scope[KEY_CHAT_ID] = chat_id

    if collection.type == CollectionType.DOCUMENT:

        if settings.CHAT_CONSUMER_IMPLEMENTATION == "document-qa":
            from kubechat.chat.websocket.document_qa_consumer import DocumentQAConsumer
            return await DocumentQAConsumer.as_asgi()(scope, receive, send)
        elif settings.CHAT_CONSUMER_IMPLEMENTATION == "fake":
            from kubechat.chat.websocket.fake_consumer import FakeConsumer
            return await FakeConsumer.as_asgi()(scope, receive, send)
        else:
            from kubechat.chat.websocket.embedding_consumer import EmbeddingConsumer
            return await EmbeddingConsumer.as_asgi()(scope, receive, send)
    elif collection.type == CollectionType.DATABASE:
        from kubechat.chat.websocket.text_2_sql_consumer import Text2SQLConsumer

        return await Text2SQLConsumer.as_asgi()(scope, receive, send)
    else:
        raise Exception("Invalid collection type")


async def web_bot_consumer_router(scope, receive, send):
    from kubechat.db.ops import query_bot
    from kubechat.db.ops import query_web_chat
    from kubechat.db.models import BotType

    path = scope["path"]
    bot_id, chat_id = extract_web_bot_and_chat_id(path)
    bot = await query_bot(None, bot_id)
    if bot is None:
        raise Exception("Collection not found")
    scope[KEY_BOT_ID] = bot_id
    scope[KEY_USER_ID] = bot.user

    chat = await query_web_chat(bot_id, chat_id)
    if chat is None:
        raise Exception("Chat not found")
    scope[KEY_CHAT_ID] = chat_id

    if bot.type == BotType.DOCUMENT_QA:
        from kubechat.chat.websocket.document_qa_consumer import DocumentQAConsumer
        return await DocumentQAConsumer.as_asgi()(scope, receive, send)
    elif bot.type == BotType.TRANSLATION:
        from kubechat.chat.websocket.translation_consumer import TranslationConsumer
        return await TranslationConsumer.as_asgi()(scope, receive, send)
    else:
        raise Exception("Invalid bot type")


websocket_urlpatterns = [
    re_path(
        r"api/v1/bots/(?P<bot_id>\w+)/chats/(?P<chat_id>\w+)/connect$",
        bot_consumer_router,
    ),
    re_path(
        r"api/v1/bots/(?P<bot_id>\w+)/web-chats/(?P<chat_id>\w+)/connect$",
        web_bot_consumer_router,
    ),
]
