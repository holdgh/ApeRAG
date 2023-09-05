import asyncio
import json
import logging
from http import HTTPStatus

from asgiref.sync import sync_to_async
from langchain.memory import RedisChatMessageHistory
from ninja import NinjaAPI

import config.settings as settings
from kubechat.utils.db import *
from kubechat.utils.request import fail, success
from .auth.validator import FeishuEventVerification
from .models import ChatPeer
from .pipeline.pipeline import BasePipeline
from .source.feishu import FeishuClient
from .utils.utils import AESCipher

logger = logging.getLogger(__name__)

api = NinjaAPI(version="1.0.0", urls_namespace="feishu")


@api.get("/spaces")
async def feishu_get_spaces(request, app_id, app_secret):
    ctx = {
        "app_id": app_id,
        "app_secret": app_secret,
    }
    result = []
    try:
        for space in FeishuClient(ctx).get_spaces():
            result.append({
                "space_id": space["id"],
                "description": space["description"],
                "name": space["name"],
            })
    except Exception as e:
        logger.exception(e)
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
    return success(result)


# using redis to cache message ids
msg_id_cache = {}


# TODO use redis to cache message ids
def message_handled(msg_id):
    if msg_id in msg_id_cache:
        return True
    else:
        msg_id_cache[msg_id] = True
        return False


@api.get("/user_access_token")
def get_user_access_token(request, code, redirect_uri):
    ctx = {
        "app_id": settings.FEISHU_APP_ID,
        "app_secret": settings.FEISHU_APP_SECRET,
    }
    client = FeishuClient(ctx)
    token = client.get_user_access_token(code, redirect_uri)
    return success({"token": token})


async def feishu_streaming_response(client, chat_id, bot, msg_id, msg):
    # TODO, don't use the auto increment id as the unique id
    try:
        chat = await query_chat_by_peer(bot.user, ChatPeer.FEISHU, chat_id)
    except Exception as e:
        chat = Chat(user=bot.user, bot=bot, peer_type=ChatPeer.FEISHU, peer_id=chat_id)
        await chat.asave()

    history = RedisChatMessageHistory(session_id=str(chat.id), url=settings.MEMORY_REDIS_URL)
    response = ""
    collection = await sync_to_async(bot.collections.first)()
    card_id = client.reply_card_message(msg_id, response)
    async for msg in BasePipeline(bot=bot, collection=collection, history=history).run(msg):
        response += msg
        client.update_card_message(card_id, response)


@api.post("/webhook/event")
async def feishu_webhook_event(request, user=None, bot_id=None):
    data = json.loads(request.body)
    bot = await query_bot(user, bot_id)
    if bot is None:
        logger.warning("bot not found: %s", bot_id)
        return
    bot_config = json.loads(bot.config)
    feishu_config = bot_config.get("feishu")

    encrypt_key = feishu_config.get("encrypt_key")
    if "encrypt" in data:
        cipher = AESCipher(encrypt_key)
        data = cipher.decrypt_string(data["encrypt"])
        data = json.loads(data)

    logger.info(data)
    if "challenge" in data:
        return {"challenge": data["challenge"]}

    if encrypt_key and not FeishuEventVerification(encrypt_key)(request):
        return fail(HTTPStatus.UNAUTHORIZED, "Unauthorized")

    header = data["header"]
    if header["event_type"] == "im.message.message_read_v1":
        return

    if header["event_type"] != "im.message.receive_v1":
        logger.warning("Unsupported event: %s", data)
        return

    event = data.get("event", None)
    if event is None:
        logger.warning("Unsupported event: %s", data)
        return

    # ignore duplicate messages
    msg_id = event["message"]["message_id"]
    if message_handled(msg_id):
        return

    content = json.loads(event["message"]["content"])
    message = content["text"]
    if message.startswith("@"):
        message = message.split(" ", 1)[1]

    if not user:
        logger.warning("invalid event without user")
        return

    app_id = feishu_config.get("app_id", "")
    app_secret = feishu_config.get("app_secret", "")
    if not app_id or not app_secret:
        logger.warning("please properly setup the feishu app id and app secret first", user, bot_id)
        return

    ctx = {
        "app_id": app_id,
        "app_secret": app_secret,
    }
    client = FeishuClient(ctx)
    chat_id = event["message"]["chat_id"]
    asyncio.create_task(feishu_streaming_response(client, chat_id, bot, msg_id, message))
    return success({"code": 0})
