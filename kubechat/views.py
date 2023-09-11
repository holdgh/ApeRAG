import io
import json
import logging
import uuid
import zipfile
import kubechat.utils.message as msg_utils
from pathlib import Path
from http import HTTPStatus

from typing import List, Optional
from kubechat.source.base import get_source
from asgiref.sync import sync_to_async
from django.http import HttpResponse
from langchain.memory import RedisChatMessageHistory
from ninja import File, NinjaAPI, Schema
from ninja.files import UploadedFile
from pydantic import BaseModel
from django.core.files.base import ContentFile
import config.settings as settings
from config.vector_db import get_vector_db_connector
from kubechat.tasks.index import add_index_for_local_document, remove_index, update_index, message_feedback
from kubechat.tasks.scan import delete_sync_documents_cron_job, \
    update_sync_documents_cron_job
from kubechat.utils.db import *
from kubechat.utils.request import fail, get_user, success
from readers.readers import DEFAULT_FILE_READER_CLS
from kubechat.tasks.sync_documents_task import sync_documents

from readers.base_embedding import get_embedding_model

from .auth.validator import GlobalHTTPAuth
from kubechat.llm.prompts import DEFAULT_MODEL_PROMPT_TEMPLATES, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2
from .models import *
from .utils.utils import generate_vector_db_collection_name, fix_path_name, validate_document_config, \
    generate_qa_vector_db_collection_name

from django.contrib.auth.models import User
from django.shortcuts import render

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


@api.post("/collections/ca/upload")
def ssl_file_upload(request, file: UploadedFile = File(...)):
    file_name = uuid.uuid4().hex
    _, file_extension = os.path.splitext(file.name)
    print(file_extension)
    if file_extension not in [".pem", ".key", ".crt", ".csr"]:
        return fail(HTTPStatus.NOT_FOUND, "file extension not found")

    if not os.path.exists(ssl_temp_file_path("")):
        os.makedirs(ssl_temp_file_path(""))

    with open(ssl_temp_file_path(file_name + file_extension), "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    return success(file_name + file_extension)


@api.post("/collections/test_connection")
def connection_test(request, connection: ConnectionInfo):
    verify = connection.verify != VerifyWay.PREFERRED
    host = connection.host

    if host == "":
        return fail(HTTPStatus.NOT_FOUND, "host not found")

    client = new_db_client(dict(connection))
    if client is None:
        return fail(HTTPStatus.NOT_FOUND, "db type not found or illegal")

    if not client.connect(
            False,
            ssl_temp_file_path(connection.ca_cert),
            ssl_temp_file_path(connection.client_key),
            ssl_temp_file_path(connection.client_cert),
    ):
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, "can not connect")

    return success("successfully connected")


@api.get("/models")
def list_model_name(request):
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
            "context_window": model_server.get("context_window", 2000),
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

    result = sync_documents.apply_async(kwargs={'collection_id': collection_id})
    sync_history_id = -1
    # keep getting information from result while running.
    while not result.ready() and sync_history_id == -1:
        if result.info is not None:
            sync_history_id = result.info.get('id', None)
    # if the task is too fast to get the info while running, use get() to get the result.
    if result.ready() and sync_history_id == -1:
        sync_history_id = result.get()
    sync_history = await CollectionSyncHistory.objects.aget(id=sync_history_id)
    return success(sync_history.view())


@api.get("/collections/{collection_id}/sync/history")
async def get_sync_histories(request, collection_id):
    user = get_user(request)
    sync_histories = await query_sync_histories(user, collection_id)
    response = []
    async for sync_history in sync_histories:
        response.append(sync_history.view())
    return success(response)


@api.get("/collections/{collection_id}/sync/{sync_history_id}")
async def get_sync_history(request, collection_id, sync_history_id):
    user = get_user(request)
    sync_history = await query_sync_history(user, collection_id, sync_history_id)
    return success(sync_history.view())


@api.post("/collections")
async def create_collection(request, collection: CollectionIn):
    user = get_user(request)
    instance = Collection(
        user=user,
        type=collection.type,
        status=CollectionStatus.ACTIVE,
        title=collection.title,
        description=collection.description,
    )

    if collection.config is not None:
        instance.config = collection.config
    await instance.asave()

    config = json.loads(collection.config)
    if instance.type == CollectionType.DATABASE:
        if config["verify"] != VerifyWay.PREFERRED:
            add_ssl_file(config, instance)
            collection.config = json.dumps(config)
            await instance.asave()
    elif instance.type == CollectionType.DOCUMENT:
        # pre-create collection in vector db
        if not validate_document_config(config):
            return fail(HTTPStatus.BAD_REQUEST, "config invalidate")
        vector_db_conn = get_vector_db_connector(
            collection=generate_vector_db_collection_name(user=user, collection=instance.id)
        )
        embedding_model = config.get("embedding_model", "")
        if not embedding_model:
            _, size = get_embedding_model(settings.EMBEDDING_MODEL, load=False)
            config["embedding_model"] = settings.EMBEDDING_MODEL
            instance.config = json.dumps(config)
            await instance.asave()
        else:
            _, size = get_embedding_model(embedding_model, load=False)
        vector_db_conn.connector.create_collection(vector_size=size)
        qa_vector_db_conn = get_vector_db_connector(
            collection=generate_qa_vector_db_collection_name(user=user, collection=instance.id)
        )
        qa_vector_db_conn.connector.create_collection(vector_size=size)
        source = get_source(json.loads(collection.config))
        if source.sync_enabled():
            sync_documents.delay(collection_id=instance.id)
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
    collections = await query_collections(user)
    response = []
    async for collection in collections:
        bots = await sync_to_async(collection.bot_set.exclude)(status=BotStatus.DELETED)
        bot_ids = []
        async for bot in bots:
            bot_ids.append(bot.id)
        response.append(collection.view(bot_ids=bot_ids))
    return success(response)


@api.get("/collections/{collection_id}/database")
async def get_database_list(request, collection_id):
    user = get_user(request)
    instance = await query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    config = json.loads(instance.config)
    db_type = config["db_type"]
    if db_type not in ["mysql", "postgresql"]:
        return fail(
            HTTPStatus.NOT_FOUND, "{} don't have multiple databases".format(db_type)
        )

    client = new_db_client(config)
    # TODO:add SSL
    if not client.connect(
            False,
    ):
        return fail(HTTPStatus.INTERNAL_SERVER_ERROR, "can not connect")

    response = client.get_database_list()
    return success(response)


@api.get("/collections/{collection_id}")
async def get_collection(request, collection_id):
    user = get_user(request)
    instance = await query_collection(user, collection_id)
    if instance is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")
    return success(instance.view())


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
    if await sync_to_async(bots.count)() > 0:
        return fail(HTTPStatus.BAD_REQUEST, "Collection has related to bots, can not be deleted")
    # TODO remove the related collection in the vector db
    collection.status = CollectionStatus.DELETED
    collection.gmt_deleted = timezone.now()
    await collection.asave()
    return success(collection.view())


@api.post("/collections/{collection_id}/documents")
async def add_document(request, collection_id, file: List[UploadedFile] = File(...)):
    user = get_user(request)
    collection = await query_collection(user, collection_id)
    if collection is None:
        return fail(HTTPStatus.NOT_FOUND, "Collection not found")

    response = []
    for item in file:
        file_suffix = os.path.splitext(item.name)[1].lower()
        if file_suffix in DEFAULT_FILE_READER_CLS.keys():
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
        else:
            logger.error("uploaded a file of unexpected file type.")
    return success(response)


@api.get("/collections/{collection_id}/documents")
async def list_documents(request, collection_id):
    user = get_user(request)
    documents = await aquery_documents(user, collection_id)
    response = []
    async for document in documents:
        response.append(document.view())
    return success(response)


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
async def add_chat(request, bot_id):
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
    chats = await query_chats(user, bot_id)
    response = []
    async for chat in chats:
        response.append(chat.view(bot_id))
    return success(response)


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

    feedbacks = await query_chat_feedbacks(user, chat_id)
    feedback_map = {}
    async for feedback in feedbacks:
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
            msg["references"] = message.additional_kwargs.get("references")
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

    feedback = await msg_utils.feedback_message(user, chat_id, message_id, msg_in.upvote, msg_in.downvote, msg_in.revised_answer)

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


@api.get("/code/codegenerate/download/{chat_id}")
async def download_code(request, chat_id):
    user = get_user(request)
    chat = await Chat.objects.exclude(status=DocumentStatus.DELETED).aget(
        user=user, pk=chat_id
    )

    @sync_to_async
    def get_collection():
        return chat.collection

    collection = await get_collection()
    if chat.user != user:
        return success("No access to the file")
    if chat.status != ChatStatus.UPLOADED:
        return success("The file is not ready for download")
    base_dir = Path(settings.CODE_STORAGE_DIR)
    buffer = io.BytesIO()
    zip = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    workspace = base_dir / "generated-code" / fix_path_name(user) / fix_path_name(
        collection.title + str(chat_id)) / "workspace"

    for root, dirs, files in os.walk(str(workspace)):
        for file in files:
            zip.write(os.path.join(root, file), arcname=file)
    zip.close()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue())
    response['Content-Disposition'] = f"attachment; filename=\"{collection.title}.zip\""
    response['Content-Type'] = 'application/zip'
    return response


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
    bots = await query_bots(user)
    response = []
    async for bot in bots:
        collections = []
        async for collection in await sync_to_async(bot.collections.all)():
            collections.append(collection.view())
        response.append(bot.view(collections))
    return success(response)


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


def index(request):
    return HttpResponse("KubeChat")


def dashboard(request):
    user_count = User.objects.count()
    collection_count = Collection.objects.count()
    document_count = Document.objects.count()
    chat_count = Chat.objects.count()
    context = {'user_count': user_count, 'Collection_count': collection_count,
               'Document_count': document_count, 'Chat_count': chat_count}
    return render(request, 'kubechat/dashboard.html', context)
