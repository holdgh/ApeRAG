import logging
import uuid
from urllib.parse import parse_qsl

from asgiref.sync import sync_to_async
from channels.generic.http import AsyncHttpConsumer
from ninja import NinjaAPI

from config import settings
from kubechat.chat.history.redis import RedisChatMessageHistory
from kubechat.chat.utils import fail_response, start_response, stop_response, success_response

logger = logging.getLogger(__name__)

api = NinjaAPI(version="1.0.0", urls_namespace="events")


class ServerSentEventsConsumer(AsyncHttpConsumer):
    async def handle(self, body):
        try:
            await self._handle(body)
        except Exception as e:
            logger.exception(e)

    async def _handle(self, body):
        from kubechat.db.models import Chat, ChatPeer
        from kubechat.db.ops import query_bot, query_chat_by_peer
        from kubechat.pipeline.knowledge_pipeline import KnowledgePipeline
        await self.send_headers(headers=[
            (b"Cache-Control", b"no-cache"),
            (b"Content-Type", b"text/event-stream"),
            (b"Transfer-Encoding", b"chunked"),
        ])
        query_params = dict(parse_qsl(self.scope['query_string'].decode('utf-8')))
        user = query_params.get("user", "")
        bot_id = query_params.get("bot_id", "")
        bot = await query_bot(user, bot_id)
        chat_id = query_params.get("chat_id", "")
        msg_id = query_params.get("msg_id", "")
        if not msg_id:
            msg_id = str(uuid.uuid4())

        if bot is None:
            event = fail_response(message_id=msg_id, error="Bot not found")
            await self.send_event(event, more_body=False)
            return

        try:
            chat = await query_chat_by_peer(bot.user, ChatPeer.FEISHU, chat_id)
            if chat is None:
                chat = Chat(user=bot.user, bot=bot, peer_type=ChatPeer.FEISHU, peer_id=chat_id)
                await chat.asave()

            msg = body.decode("utf-8")
            collection = await sync_to_async(bot.collections.first)()
            history = RedisChatMessageHistory(session_id=str(chat.id), url=settings.MEMORY_REDIS_URL)

            event = start_response(message_id=msg_id)
            await self.send_event(event)

            async for msg in KnowledgePipeline(bot=bot, collection=collection, history=history).run(msg, message_id=msg_id):
                event = success_response(message_id=msg_id, data=msg)
                await self.send_event(event)

            event = stop_response(message_id=msg_id, references=[])
            await self.send_event(event, more_body=False)
        except Exception as e:
            logger.exception(e)
            event = fail_response(message_id=msg_id, error=str(e))
            await self.send_event(event, more_body=False)

    async def send_event(self, event: str, more_body=True):
        event = event + "\n"
        await self.send_body(event.encode("utf-8"), more_body=more_body)
