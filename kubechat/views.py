import datetime
import json
import logging
from http import HTTPStatus
from typing import List, Optional

from asgiref.sync import sync_to_async
from celery.result import GroupResult
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.shortcuts import render
from langchain.memory import RedisChatMessageHistory
from ninja import File, NinjaAPI, Schema
from ninja.files import UploadedFile

import config.settings as settings
import kubechat.utils.message as msg_utils
from config.celery import app
from kubechat.llm.prompts import DEFAULT_MODEL_PROMPT_TEMPLATES, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2
from kubechat.source.base import get_source
from kubechat.source.url import download_web_text_to_temp_file
from kubechat.tasks.collection import init_collection_task, delete_collection_task
from kubechat.tasks.index import add_index_for_local_document, remove_index, update_index, message_feedback
from kubechat.tasks.scan import delete_sync_documents_cron_job, \
    update_sync_documents_cron_job
from kubechat.tasks.sync_documents_task import sync_documents, get_sync_progress
from kubechat.utils.db import *
from kubechat.utils.request import fail, get_user, success,get_urls
from readers.readers import DEFAULT_FILE_READER_CLS
from .auth.validator import GlobalHTTPAuth
from .models import *
from .utils.utils import validate_source_connect_config, validate_bot_config

logger = logging.getLogger(__name__)

api = NinjaAPI(version="1.0.0", auth=GlobalHTTPAuth(), urls_namespace="collection")


class CollectionIn(Schema):
    title: str
    type: str
    description: Optional[str]
    config: Optional[str]


class DocumentIn(Schema):
    name: str
    config: Optional[str]


class ConnectionInfo(Schema):
    db_type: str
    host: str
    port: Optional[int]
    db_name: Optional[str]
    username: Optional[str]
    password: Optional[str]
    verify: VerifyWay
    ca_cert: Optional[str]
    client_key: Optional[str]
    client_cert: Optional[str]


class Auth(BaseModel):
    username: str = ""
    password: str = ""


class Host(BaseModel):
    source: str = "system"
    host: str = ""
    port: str = ""


class DocumentConfig(BaseModel):
    host: Host = Host
    auth: Auth = Auth
    filedir: str = ""
    filepath: str = ""


@api.get("/models")
def list_models(request):
    response = []
    model_servers = json.loads(settings.MODEL_SERVERS)
    if model_servers is None:
        return fail(HTTPStatus.NOT_FOUND, "model name not found")
    for model_server in model_servers:
        response.append({
            "value": model_server["name"],
            "label": model_server.get("label", model_server["name"]),
            "enabled": model_server.get("enabled", "true").lower() == "true",
            "prompt_template": DEFAULT_MODEL_PROMPT_TEMPLATES.get(model_server["name"],
                                                                  DEFAULT_CHINESE_PROMPT_TEMPLATE_V2),
            "context_window": model_server.get("context_window", 3500),
        })
    response.sort(key=lambda x: x["enabled"], reverse=True)
    return success(response)


@api.post("/collections/{collection_id}/sync")
async def sync_immediately(request, collection_id):
    user = get_user(request)
    collection = await query_collection(user, collection_id)
    source = get_source(json.loads(collection.config))
    if not source.sync_enabled():
        return fail(HTTPStatus.BAD_REQUEST, "source type not supports sync")

    pr = await query_running_sync_histories(user, collection_id)
    async for task in pr.data:
        return fail(HTTPStatus.BAD_REQUEST, f"have running sync task {task.id}, please cancel it first")

    instance = CollectionSyncHistory(
        user=collection.user,
        start_time=timezone.now(),
        collection=collection,
        execution_time=datetime.timedelta(seconds=0),
        total_documents_to_sync=0,
        status=CollectionSyncStatus.RUNNING,
    )
    await instance.asave()
    sync_documents.delay(collection_id=collection_id, sync_history_id=instance.id)
    return success(instance.view())


@api.post("/collections/{collection_id}/cancel_sync/{collection_sync_id}")
async def cancel_sync(request, collection_id, collection_sync_id):
    """
    cancel the collection_sync_id related tasks

    Note that if using gevent/eventlet as the worker pool, the cancel operation is not work
    Please refer to https://github.com/celery/celery/issues/4019

    """
    user = get_user(request)
    sync_history = await query_sync_history(user, collection_id, collection_sync_id)
    task_context = sync_history.task_context
    if task_context is None:
        return fail(HTTPStatus.BAD_REQUEST, f"no task context in sync history {collection_sync_id}")

    # revoke the scan task
    scan_task_id = task_context["scan_task_id"]
    if scan_task_id is None:
        return fail(HTTPStatus.BAD_REQUEST, f"no scan task id in sync history {collection_sync_id}")
    app.AsyncResult(scan_task_id).revoke(terminate=True)

    # revoke the index tasks
    group_id = sync_history.task_context.get("index_task_group_id", "")
    if group_id:
        group_result = GroupResult.restore(group_id, app=app)
        for task in group_result.results:
            task = app.AsyncResult(task.id)
            task.revoke(terminate=True)
    else:
        logger.warning(f"no index task group id in sync history {collection_sync_id}")

    sync_history.status = CollectionSyncStatus.CANCELED
    await sync_history.asave()
    return success({})


@api.get("/collections/{collection_id}/sync/history")
async def list_sync_histories(request, collection_id):
    user = get_user(request)
    pr = await query_sync_histories(user, collection_id, build_pq(request))
    response = []
    async for sync_history in pr.data:
        if sync_history.status == CollectionSyncStatus.RUNNING:
            progress = get_sync_progress(sync_history)
            sync_history.failed_documents = progress.failed_documents
            sync_history.successful_documents = progress.successful_documents
            sync_history.processing_documents = progress.processing_documents
            sync_history.pending_documents = progress.pending_documents
        response.append(sync_history.view())
    return success(response, pr)


@api.get("/collections/{collection_id}/sync/{sync_history_id}")
async def get_sync_history(request, collection_id, sync_history_id):
    user = get_user(request)
    sync_history = await query_sync_history(user, collection_id, sync_history_id)
    if sync_history.status == CollectionSyncStatus.RUNNING:
        progress = get_sync_progress(sync_history)
        sync_history.failed_documents = progress.failed_documents
        sync_history.successful_documents = progress.successful_documents
        sync_history.processing_documents = progress.processing_documents
        sync_history.pending_documents = progress.pending_documents
    return success(sync_history.view())


@api.post("/collections")
async def create_collection(request, collection: CollectionIn):
    user = get_user(request)
    config = json.loads(collection.config)
    if collection.type == CollectionType.DOCUMENT:
        is_validate, error_msg = validate_source_connect_config(config)
        if not is_validate:
            return fail(HTTPStatus.BAD_REQUEST, error_msg)
    instance = Collection(
        user=user,
        type=collection.type,
        status=CollectionStatus.INACTIVE,
        title=collection.title,
        description=collection.description,
    )

    if collection.config is not None:
        instance.config = collection.config
    await instance.asave()

    if instance.type == CollectionType.DATABASE:
        if config["verify"] != VerifyWay.PREFERRED:
            add_ssl_file(config, instance)
            collection.config = json.dumps(config)
            await instance.asave()
    elif instance.type == CollectionType.DOCUMENT :
        init_collection_task.delay(collection_id=instance.id)
    elif instance.type == CollectionType.CODE:
        chat = Chat(
            user=instance.user,
            status=ChatStatus.ACTIVE,
            collection=instance,
            summary=instance.description,
        )
        await chat.asave()
    else:
        return fail(HTTPStatus.BAD_REQUEST, "unknown collection type")

    return success(instance.view())


@api.get("/collections")
async def list_collections(request):
    user = get_user(request)
    pr = await query_collections(user, build_pq(request))
    response = []
    async for collection in pr.data:
        response.append(collection.view())
    return success(response, pr)


@api.get("/default_collections")
async def list_default_collections(request):
    pr = await query_collections(settings.SYSTEM_USER, build_pq(request))
    response = []
    async for collection in pr.data:
        response.append(collection.view())
    return success(response, pr)


@api.get("/collections/{collection_id}")
async def get_collection(request, collection_id):
    user = get_user(request)
    instance = await query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    bots = await sync_to_async(instance.bot_set.exclude)(status=BotStatus.DELETED)
    bot_ids = []
    async for bot in bots:
        bot_ids.append(bot.id)
    return success(instance.view(bot_ids=bot_ids))


@api.put("/collections/{collection_id}")
async def update_collection(request, collection_id, collection: CollectionIn):
    user = get_user(request)
    instance = await query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    instance.title = collection.title
    instance.description = collection.description
    instance.config = collection.config
    await instance.asave()
    source = get_source(json.loads(collection.config))
    if source.sync_enabled():
        await update_sync_documents_cron_job(instance.id)

    bots = await sync_to_async(instance.bot_set.exclude)(status=BotStatus.DELETED)
    bot_ids = []
    async for bot in bots:
        bot_ids.append(bot.id)

    return success(instance.view(bot_ids=bot_ids))


@api.delete("/collections/{collection_id}")
async def delete_collection(request, collection_id):
    user = get_user(request)
    collection = await query_collection(user, collection_id)
    if collection is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    await delete_sync_documents_cron_job(collection.id)
    bots = await sync_to_async(collection.bot_set.exclude)(status=BotStatus.DELETED)
    bot_ids = []
    async for bot in bots:
        bot_ids.append(bot.id)
    if len(bot_ids) > 0:
        return fail(HTTPStatus.BAD_REQUEST, f"Collection has related to bots {','.join(bot_ids)}, can not be deleted")
    collection.status = CollectionStatus.DELETED
    collection.gmt_deleted = timezone.now()
    await collection.asave()
    delete_collection_task.delay(collection_id)
    return success(collection.view())


@api.post("/collections/{collection_id}/documents")
async def create_document(request, collection_id, file: List[UploadedFile] = File(...)):
    user = get_user(request)
    collection = await query_collection(user, collection_id)
    if collection is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    response = []
    for item in file:
        file_suffix = os.path.splitext(item.name)[1].lower()
        if file_suffix not in DEFAULT_FILE_READER_CLS.keys():
            return fail(HTTPStatus.BAD_REQUEST, f"unsupported file type {file_suffix}")

        try:
            document_instance = Document(
                user=user,
                name=item.name,
                status=DocumentStatus.PENDING,
                size=item.size,
                collection=collection,
                file=ContentFile(item.read(), item.name),
            )
            await document_instance.asave()
            document_instance.metadata = json.dumps({
                "path": document_instance.file.path,
            })
            await document_instance.asave()
            response.append(document_instance.view())
            add_index_for_local_document.delay(document_instance.id)
        except IntegrityError:
            return fail(HTTPStatus.BAD_REQUEST, f"document {item.name} already exists")
        except Exception as e:
            logger.exception("add document failed")
            return fail(HTTPStatus.INTERNAL_SERVER_ERROR, "add document failed")
    return success(response)


@api.post("/collections/{collection_id}/urls")
async def create_url_document(request, collection_id):
    user = get_user(request)
    response = []
    collection = await query_collection(user, collection_id)
    urls = get_urls(request)
    if collection is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    try:
        for url in urls:
            document_instance = Document(
                user=user,
                name=url + '.txt',
                status=DocumentStatus.PENDING,
                collection=collection,
                size=0,
            )
            await document_instance.asave()
            string_data = json.dumps(url)
            document_instance.metadata = json.dumps({
                "url": string_data,
            })
            await document_instance.asave()
            add_index_for_local_document.delay(document_instance.id)

    except IntegrityError as e:
        return fail(HTTPStatus.BAD_REQUEST, f"document {document_instance.name}  " + e)
    except Exception as e:
        logger.exception("add document failed")
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, "add document failed")
    return success(response)

@api.get("/collections/{collection_id}/documents")
async def list_documents(request, collection_id):
    user = get_user(request)
    pr = await query_documents(user, collection_id, build_pq(request))
    response = []
    async for document in pr.data:
        response.append(document.view())
    return success(response, pr)


@api.put("/collections/{collection_id}/documents/{document_id}")
async def update_document(
        request, collection_id, document_id, document: DocumentIn):
    user = get_user(request)
    instance = await query_document(user, collection_id, document_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Document not found")

    if document.config:
        try:
            config = json.loads(document.config)
            metadata = json.loads(instance.metadata)
            metadata["labels"] = config["labels"]
            instance.metadata = json.dumps(metadata)
        except Exception:
            return fail(HTTPStatus.BAD_REQUEST, "invalid document config")
    await instance.asave()
    # if user add labels for a document, we need to update index
    update_index.delay(instance.id)
    return success(instance.view())


@api.delete("/collections/{collection_id}/documents/{document_id}")
async def delete_document(request, collection_id, document_id):
    user = get_user(request)
    document = await query_document(user, collection_id, document_id)
    if document is None:
        return fail(HTTPStatus.NOT_FOUND, "Document not found")
    remove_index.delay(document.id)
    return success(document.view())


@api.post("/bots/{bot_id}/chats")
async def create_chat(request, bot_id):
    user = get_user(request)
    bot = await query_bot(user, bot_id)
    if bot is None:
        return fail(HTTPStatus.NOT_FOUND, "Bot not found")
    instance = Chat(user=user, bot=bot)
    await instance.asave()
    return success(instance.view(bot_id))


@api.get("/bots/{bot_id}/chats")
async def list_chats(request, bot_id):
    user = get_user(request)
    pr = await query_chats(user, bot_id, build_pq(request))
    response = []
    async for chat in pr.data:
        response.append(chat.view(bot_id))
    return success(response, pr)


@api.put("/bots/{bot_id}/chats/{chat_id}")
async def update_chat(request, bot_id, chat_id):
    user = get_user(request)
    chat = await query_chat(user, bot_id, chat_id)
    if chat is None:
        return fail(HTTPStatus.NOT_FOUND, "Chat not found")
    chat.summary = ""
    await chat.asave()
    history = RedisChatMessageHistory(chat_id, settings.MEMORY_REDIS_URL)
    history.clear()
    return success(chat.view(bot_id))


@api.get("/bots/{bot_id}/chats/{chat_id}")
async def get_chat(request, bot_id, chat_id):
    user = get_user(request)
    chat = await query_chat(user, bot_id, chat_id)
    if chat is None:
        return fail(HTTPStatus.NOT_FOUND, "Chat not found")

    pr = await query_chat_feedbacks(user, chat_id)
    feedback_map = {}
    async for feedback in pr.data:
        feedback_map[feedback.message_id] = feedback

    history = RedisChatMessageHistory(chat_id, url=settings.MEMORY_REDIS_URL)
    messages = []
    for message in history.messages:
        try:
            item = json.loads(message.content)
        except Exception as e:
            logger.exception(e)
            continue
        role = message.additional_kwargs.get("role", "")
        if not role:
            continue
        msg = {
            "id": item["id"],
            "type": "message",
            "timestamp": item["timestamp"],
            "role": role,
        }
        if role == "human":
            msg["data"] = item["query"]
        else:
            msg["data"] = item["response"]
            msg["references"] = item.get("references")
        feedback = feedback_map.get(item.get("id", ""), None)
        if role == "ai" and feedback:
            msg["upvote"] = feedback.upvote
            msg["downvote"] = feedback.downvote
            msg["revised_answer"] = feedback.revised_answer
            msg["feed_back_status"] = feedback.status
        messages.append(msg)
    return success(chat.view(bot_id, messages))


class MessageFeedbackIn(Schema):
    upvote: Optional[int]
    downvote: Optional[int]
    revised_answer: Optional[str]


@api.post("/bots/{bot_id}/chats/{chat_id}/messages/{message_id}")
async def feedback_message(request, bot_id, chat_id, message_id, msg_in: MessageFeedbackIn):
    user = get_user(request)

    feedback = await msg_utils.feedback_message(user, chat_id, message_id, msg_in.upvote, msg_in.downvote,
                                                msg_in.revised_answer)

    # embedding the revised answer
    if msg_in.revised_answer is not None:
        message_feedback.delay(feedback_id=feedback.id)
    return success({})


@api.delete("/bots/{bot_id}/chats/{chat_id}")
async def delete_chat(request, bot_id, chat_id):
    user = get_user(request)
    chat = await query_chat(user, bot_id, chat_id)
    if chat is None:
        return fail(HTTPStatus.NOT_FOUND, "Chat not found")
    chat.status = ChatStatus.DELETED
    chat.gmt_deleted = timezone.now()
    await chat.asave()
    history = RedisChatMessageHistory(chat_id, settings.MEMORY_REDIS_URL)
    history.clear()
    return success(chat.view())


class BotIn(Schema):
    title: str
    description: Optional[str]
    config: Optional[str]
    collection_ids: Optional[List[str]]


@api.post("/bots")
async def create_bot(request, bot_in: BotIn):
    user = get_user(request)
    bot = Bot(
        user=user,
        title=bot_in.title,
        status=BotStatus.ACTIVE,
        description=bot_in.description,
        config=bot_in.config,
    )
    config = json.loads(bot_in.config)
    model = config.get("model")
    llm_config = config.get("llm")
    valid, msg = validate_bot_config(model, llm_config)
    if not valid:
        return fail(HTTPStatus.BAD_REQUEST, msg)
    await bot.asave()
    collections = []
    for cid in bot_in.collection_ids:
        collection = await query_collection(user, cid)
        if not collection:
            return fail(HTTPStatus.NOT_FOUND, "Collection %s not found" % cid)
        await sync_to_async(bot.collections.add)(collection)
        collections.append(collection.view())
    await bot.asave()
    return success(bot.view(collections))


@api.get("/bots")
async def list_bots(request):
    user = get_user(request)
    pr = await query_bots(user, build_pq(request))
    response = []
    async for bot in pr.data:
        collections = []
        async for collection in await sync_to_async(bot.collections.all)():
            collections.append(collection.view())
        response.append(bot.view(collections))
    return success(response, pr)


@api.get("/bots/{bot_id}")
async def get_bot(request, bot_id):
    user = get_user(request)
    bot = await query_bot(user, bot_id)
    if bot is None:
        return fail(HTTPStatus.NOT_FOUND, "Bot not found")
    collections = []
    async for collection in await sync_to_async(bot.collections.all)():
        collections.append(collection.view())
    return success(bot.view(collections))


@api.put("/bots/{bot_id}")
async def update_bot(request, bot_id, bot_in: BotIn):
    user = get_user(request)
    bot = await query_bot(user, bot_id)
    if bot is None:
        return fail(HTTPStatus.NOT_FOUND, "Bot not found")
    config = json.loads(bot_in.config)
    model = config.get("model")
    llm_config = config.get("llm")
    valid, msg = validate_bot_config(model, llm_config)
    if not valid:
        return fail(HTTPStatus.BAD_REQUEST, msg)
    bot.title = bot_in.title
    bot.description = bot_in.description
    bot.config = bot_in.config
    await sync_to_async(bot.collections.clear)()
    for cid in bot_in.collection_ids:
        collection = await query_collection(user, cid)
        if not collection:
            return fail(HTTPStatus.NOT_FOUND, "Collection %s not found" % cid)
        await sync_to_async(bot.collections.add)(collection)
    await bot.asave()
    collections = []
    async for collection in await sync_to_async(bot.collections.all)():
        collections.append(collection.view())
    return success(bot.view(collections))


@api.delete("/bots/{bot_id}")
async def delete_bot(request, bot_id):
    user = get_user(request)
    bot = await query_bot(user, bot_id)
    if bot is None:
        return fail(HTTPStatus.NOT_FOUND, "Bot not found")
    bot.status = BotStatus.DELETED
    bot.gmt_deleted = timezone.now()
    await bot.asave()
    return success(bot.view())


def default_page(request, exception):
    return render(request, '404.html')


def dashboard(request):
    user_count = User.objects.count()
    collection_count = Collection.objects.count()
    document_count = Document.objects.count()
    chat_count = Chat.objects.count()
    context = {'user_count': user_count, 'Collection_count': collection_count,
               'Document_count': document_count, 'Chat_count': chat_count}
    return render(request, 'kubechat/dashboard.html', context)
