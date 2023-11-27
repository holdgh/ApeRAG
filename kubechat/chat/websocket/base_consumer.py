import json
import logging
import traceback
from abc import abstractmethod

import websockets
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain.memory import RedisChatMessageHistory

import config.settings as settings
from kubechat.auth.validator import DEFAULT_USER
from kubechat.chat.utils import start_response, success_response, stop_response, fail_response
from kubechat.pipeline.pipeline import KUBE_CHAT_DOC_QA_REFERENCES, KeywordPipeline
from kubechat.db.ops import query_bot
from kubechat.utils.utils import now_unix_milliseconds
from kubechat.utils.constant import KEY_USER_ID, KEY_BOT_ID, KEY_CHAT_ID, KEY_WEBSOCKET_PROTOCOL
from readers.base_embedding import get_collection_embedding_model

logger = logging.getLogger(__name__)


class BaseConsumer(AsyncWebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.collection_id = None
        self.embedding_model = None
        self.vector_size = 0
        self.history = None
        self.user = DEFAULT_USER
        self.collection = None
        self.bot = None

    async def connect(self):

        self.user = self.scope[KEY_USER_ID]
        bot_id = self.scope[KEY_BOT_ID]
        chat_id = self.scope[KEY_CHAT_ID]
        self.bot = await query_bot(self.user, bot_id)
        self.collection = await sync_to_async(self.bot.collections.first)()
        self.collection_id = self.collection.id
        # collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        # self.collection_id = collection_id
        # collection = await query_collection(self.user, collection_id)
        # if collection is None:
        #     raise Exception("Collection not found")
        # self.collection = collection

        self.embedding_model, self.vector_size = get_collection_embedding_model(self.collection)
        self.history = RedisChatMessageHistory(
            session_id=chat_id, url=settings.MEMORY_REDIS_URL
        )

        # If using daphne, we need to put the token in the headers and include the headers in the subprotocol.
        # headers = {}
        # token = self.scope.get("Sec-Websocket-Protocol", None)
        # if token is not None:
        #     headers = {"SEC-WEBSOCKET-PROTOCOL": token}
        # await self.accept(subprotocol=(None, headers))

        # If using uvicorn, we need to put the token in the headers and include the headers in the message as uvicorn
        # by extracting the headers from the message.
        # To customize the message layout, we need to call the send method in the AsyncWebsocketConsumer class.
        headers = []
        token = self.scope.get(KEY_WEBSOCKET_PROTOCOL, None)
        if token is not None:
            headers.append((KEY_WEBSOCKET_PROTOCOL.encode("ascii"), token.encode("ascii")))
        await super(AsyncWebsocketConsumer, self).send({"type": "websocket.accept", "headers": headers})
        self.pipeline = KeywordPipeline(bot=self.bot, collection=self.collection, history=self.history)

    async def disconnect(self, close_code):
        pass

    @abstractmethod
    def predict(self, query, **kwargs):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        self.msg_type = data["type"]
        self.response_type = "message"

        message = ""
        references = []
        message_id = f"{now_unix_milliseconds()}"

        try:
            # send start message
            await self.send(text_data=start_response(message_id))

            async for tokens in self.predict(data["data"], message_id=message_id):
                if tokens.startswith(KUBE_CHAT_DOC_QA_REFERENCES):
                    references = json.loads(tokens[len(KUBE_CHAT_DOC_QA_REFERENCES):])
                    continue

                # streaming response
                response = success_response(
                    message_id, tokens, issql=self.response_type == "sql"
                )
                await self.send(text_data=response)

                # concat response tokens
                message += tokens

        except websockets.exceptions.ConnectionClosedError:
            logger.warning("Connection closed")
        except Exception as e:
            logger.warning("[Oops] %s: %s", str(e), traceback.format_exc())
            await self.send(text_data=fail_response(message_id, str(e)))
        finally:
            # send stop message
            await self.send(text_data=stop_response(message_id, references, self.pipeline.memory_count))


