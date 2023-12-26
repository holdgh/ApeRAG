import hmac
import hashlib
import base64
import asyncio
import json
import time
from datetime import datetime

from ninja import Router
from config import settings
import redis.asyncio as redis
import kubechat.chat.message

from kubechat.apps import QuotaType
from kubechat.chat.history.redis import RedisChatMessageHistory
from kubechat.pipeline.pipeline import KeywordPipeline
from kubechat.db.ops import *
import openai
import os
import requests
from django.http import JsonResponse
from kubechat.views.utils import  success,fail


logger = logging.getLogger(__name__)

router = Router()

@router.post("/webhook/event")
async def post(request,user,bot_id):
    bot = await query_bot(user, bot_id)
    bot_config = json.loads(bot.config)
    secret=bot_config['dingtalk']['client_secret']
    if validate_sign(request.headers['Timestamp'], client_secret=secret, request_sign=request.headers['Sign']):
        data = json.loads(request.body.decode('utf-8'))
        # sender_nick = data.get('senderNick')
        message_content = data.get('text', {}).get('content')
        sender_id = data.get('senderStaffId')
        session_webhook=data.get('sessionWebhook')
        msg_id=data.get('msgId')
        redis_client = redis.Redis.from_url(settings.MEMORY_REDIS_URL)
        if bot is None:
            logger.warning("bot not found: %s", bot_id)
            asyncio.create_task(send_message("bot not found",session_webhook,sender_id))
            return
        asyncio.create_task(send_message(f"我已经收到问题\"{message_content}\"啦，正在飞速生成回答中", session_webhook, sender_id))
        asyncio.create_task(dingtalk_text_response(redis_client,user,bot,message_content,msg_id,sender_id,session_webhook))
        return success("")

    return fail(400,"validate dingtalk sign failed")


def validate_sign(timestamp, client_secret, request_sign):
    client_secret_enc = client_secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, client_secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(client_secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign==request_sign

async def dingtalk_text_response(redis_client, user, bot, query, msg_id,sender_id,session_webhook):
    chat_id = user
    chat = await query_chat_by_peer(bot.user, ChatPeer.DINGTALK, chat_id)
    if chat is None:
        chat = Chat(user=bot.user, bot=bot, peer_type=ChatPeer.DINGTALK, peer_id=chat_id)
        await chat.asave()

    history = RedisChatMessageHistory(session_id=str(chat.id), url=settings.MEMORY_REDIS_URL)
    collection = await sync_to_async(bot.collections.first)()
    response = ""

    pipeline = KeywordPipeline(bot=bot, collection=collection, history=history)
    use_default_token = pipeline.predictor.use_default_token

    conversation_limit = await query_user_quota(user, QuotaType.MAX_CONVERSATION_COUNT)

    try:
        if use_default_token and conversation_limit:
            if not await check_quota_usage(redis_client, bot.user, conversation_limit):
                error = f"conversation rounds have reached to the limit of {conversation_limit}"
                await send_message(error, user,sender_id)
                return


        async for msg in pipeline.run(query, message_id=msg_id):
            response += msg

        max_length = 2048
        for i in range(0, len(response), max_length):
            message = response[i:i + max_length]
            await notify_dingding(query,message, webhook=session_webhook,sender_id=sender_id)
    except Exception as e:
        logger.exception(e)
    finally:
        if use_default_token and conversation_limit:
            await manage_quota_usage(redis_client, bot.user, conversation_limit)

async def notify_dingding(question,answer,webhook,sender_id):
    data = {
        "msgtype": "text",
        "at": {
            "atUserIds": [
                f"{sender_id}"
            ],
            "isAtAll": False
        },
        "text": {
            "content": f"Q:{question}\n"
                       f"A:{answer}"
        }

    }
    try:
        r = requests.post(webhook, json=data)
        reply = r.json()
        logger.info("dingding: " + str(reply))
    except Exception as e:
        logger.error(e)
async def send_message(msg,webhook,sender_id):
    data = {
        "msgtype": "text",
        "text": {
            "content": f"{msg}"
        },

        "at": {
            "atUserIds": [
                sender_id
            ],
            "isAtAll": False
        }
    }
    try:
        r = requests.post(webhook, json=data)
        reply = r.json()
        logger.info("dingding: " + str(reply))
    except Exception as e:
        logger.error(e)

async def check_quota_usage(redis_client, user, conversation_limit):
    key = "conversation_history:" + user

    if await redis_client.exists(key):
        if int(await redis_client.get(key)) >= conversation_limit:
            return False
    return True
async def manage_quota_usage(redis_client, user, conversation_limit):
    key = "conversation_history:" + user

    # already used kubechat today
    if await redis_client.exists(key):
        if int(await redis_client.get(key)) < conversation_limit:
            await redis_client.incr(key)
    # first time to use kubechat today
    else:
        now = datetime.now()
        end_of_today = datetime(now.year, now.month, now.day, 23, 59, 59)
        await redis_client.set(key, 1)
        await redis_client.expireat(key, int(end_of_today.timestamp()))