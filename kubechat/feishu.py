import asyncio
import json
import logging
from http import HTTPStatus
from typing import Optional

import requests
from asgiref.sync import sync_to_async
from langchain import PromptTemplate
from ninja import NinjaAPI

import config.settings as settings
from kubechat.utils.db import *
from kubechat.utils.request import fail, success
from query.query import QueryWithEmbedding
from readers.base_embedding import get_default_embedding_model
from vectorstore.connector import VectorStoreConnectorAdaptor
from .auth.validator import FeishuEventVerification
from .source.feishu import FeishuClient
from .utils.utils import generate_vector_db_collection_id, AESCipher
from kubechat.chat.prompts import DEFAULT_MODEL_PROMPT_TEMPLATES, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2

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


async def predict(user, collection_id, query, embedding_model):
    vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
    vector_db_collection_id = generate_vector_db_collection_id(user, collection_id)
    vectordb_ctx["collection"] = vector_db_collection_id
    adaptor = VectorStoreConnectorAdaptor(settings.VECTOR_DB_TYPE, vectordb_ctx)
    vector = embedding_model.get_text_embedding(query)
    query_embedding = QueryWithEmbedding(query=query, top_k=3, embedding=vector)

    results = adaptor.connector.search(
        query_embedding,
        collection_name=vector_db_collection_id,
        query_vector=query_embedding.embedding,
        with_vectors=True,
        limit=query_embedding.top_k,
        consistency="majority",
        search_params={"hnsw_ef": 128, "exact": False},
        score_threshold=0.5,
    )

    query_context = results.get_packed_answer(1900)

    collection = await query_collection(user, collection_id)
    config = json.loads(collection.config)
    model = config.get("model", "")

    prompt_template = DEFAULT_MODEL_PROMPT_TEMPLATES.get(model, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2)
    prompt = PromptTemplate.from_template(prompt_template)
    prompt_str = prompt.format(query=query, context=query_context)

    input = {
        "prompt": prompt_str,
        "temperature": 0,
        "max_new_tokens": 2048,
        "model": model,
        "stop": "\nSQLResult:",
    }

    # choose llm model
    model_servers = json.loads(settings.MODEL_SERVERS)
    if len(model_servers) == 0:
        raise Exception("No model server available")
    endpoint = model_servers[0]["endpoint"]
    for model_server in model_servers:
        model_name = model_server["name"]
        model_endpoint = model_server["endpoint"]
        if model == model_name:
            endpoint = model_endpoint
            break

    response = requests.post("%s/generate_stream" % endpoint, json=input, stream=True, )
    buffer = ""
    for c in response.iter_content():
        if c == b"\x00":
            continue

        c = c.decode("utf-8")
        buffer += c

        if "}" in c:
            idx = buffer.rfind("}")
            data = buffer[: idx + 1]
            try:
                msg = json.loads(data)
            except Exception as e:
                continue
            yield msg["text"]
            await asyncio.sleep(0.1)
            buffer = buffer[idx + 1:]


@api.get("/user_access_token")
def get_user_access_token(request, code, redirect_uri):
    ctx = {
        "app_id": settings.FEISHU_APP_ID,
        "app_secret": settings.FEISHU_APP_SECRET,
    }
    client = FeishuClient(ctx)
    token = client.get_user_access_token(code, redirect_uri)
    return success({"token": token})


async def feishu_streaming_response(client, user, collection_id, msg_id, msg):
    model, _ = get_default_embedding_model()
    response = ""
    card_id = client.reply_card_message(msg_id, response)
    async for token in predict(user, collection_id, msg, model):
        response += token
        client.update_card_message(card_id, response)


@api.post("/webhook/event")
async def feishu_webhook_event(request, user=None, bot_id=None):
    data = json.loads(request.body)
    bot = await query_bot(user, bot_id)
    if bot is None:
        logger.warning("bot not found: %s", bot_id)
        return
    config = json.loads(bot.config)
    feishu_config = config.get("feishu")

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

    collection = await sync_to_async(bot.collections.first)()
    if not collection:
        logger.warning("invalid event without collection_id")
        return

    collection_config = json.loads(collection.config)
    ctx = {
        "app_id": collection_config.get("app_id", ""),
        "app_secret": collection_config.get("app_secret", ""),
    }
    client = FeishuClient(ctx)

    asyncio.create_task(feishu_streaming_response(client, user, collection.id, msg_id, message))
    return success({"code": 0})
