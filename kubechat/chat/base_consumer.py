import datetime
import json
import logging
import traceback

import websockets
from abc import abstractmethod
from asgiref.sync import sync_to_async, async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, AsyncConsumer
from langchain.memory import RedisChatMessageHistory
from langchain.schema import AIMessage, BaseChatMessageHistory, HumanMessage

import config.settings as settings
from kubechat.auth.validator import DEFAULT_USER
from kubechat.utils.db import query_bot
from kubechat.utils.utils import extract_collection_and_chat_id, now_unix_milliseconds, extract_bot_and_chat_id
from readers.base_embedding import get_default_embedding_model, get_collection_embedding_model

logger = logging.getLogger(__name__)


KUBE_CHAT_DOC_QA_REFERENCES = "|KUBE_CHAT_DOC_QA_REFERENCES|"


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
        from kubechat.utils.db import query_chat, query_collection

        self.user = self.scope["X-USER-ID"]
        bot_id, chat_id = extract_bot_and_chat_id(self.scope["path"])
        self.bot = await query_bot(self.user, bot_id)
        self.collection = await sync_to_async(self.bot.collections.first)()
        self.collection_id = self.collection.id
        # collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        # self.collection_id = collection_id
        # collection = await query_collection(self.user, collection_id)
        # if collection is None:
        #     raise Exception("Collection not found")
        # self.collection = collection

        chat = await query_chat(self.user, bot_id, chat_id)
        if chat is None:
            raise Exception("Chat not found")

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
        token = self.scope.get("Sec-Websocket-Protocol", None)
        if token is not None:
            headers.append((b"Sec-Websocket-Protocol", token.encode("ascii")))
        await super(AsyncWebsocketConsumer, self).send({"type": "websocket.accept", "headers": headers})

    async def disconnect(self, close_code):
        pass

    @abstractmethod
    def predict(self, query):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        self.msg_type = data["type"]
        self.response_type = "message"

        # save user message to history
        if self.msg_type != "sql":
            self.history.add_message(
                HumanMessage(content=text_data, additional_kwargs={"role": "human"})
            )

        message = ""
        message_id = f"{now_unix_milliseconds()}"

        try:
            # send start message
            await self.send(text_data=self.start_response(message_id))

            references = []
            async for tokens in self.predict(data["data"]):
                if tokens.startswith(KUBE_CHAT_DOC_QA_REFERENCES):
                    references = json.loads(tokens[len(KUBE_CHAT_DOC_QA_REFERENCES) :])
                    continue

                # streaming response
                response = self.success_response(
                    message_id, tokens, issql=self.response_type == "sql"
                )
                await self.send(text_data=response)

                # concat response tokens
                message += tokens

            # send stop message
            await self.send(text_data=self.stop_response(message_id, references))

            # save all tokens as a message to history
            self.history.add_message(
                AIMessage(
                    content=self.success_response(
                        message_id, message, issql=self.response_type == "sql"
                    ),
                    additional_kwargs={"role": "ai", "references": references},
                )
            )
        except websockets.exceptions.ConnectionClosedError:
            logger.warning("Connection closed")
        except Exception as e:
            logger.warning("%s: %s", str(e), traceback.format_exc())

    @staticmethod
    def success_response(message_id, data, issql=False):
        return json.dumps(
            {
                "type": "message" if not issql else "sql",
                "id": message_id,
                "data": data,
                "timestamp": now_unix_milliseconds(),
            }
        )

    @staticmethod
    def fail_response(message_id, error):
        return json.dumps(
            {
                "type": "error",
                "id": message_id,
                "data": error,
                "timestamp": now_unix_milliseconds(),
            }
        )

    @staticmethod
    def start_response(message_id):
        return json.dumps(
            {
                "type": "start",
                "id": message_id,
                "timestamp": now_unix_milliseconds(),
            }
        )

    @staticmethod
    def stop_response(message_id, references):
        if references is None:
            references = []
        return json.dumps(
            {
                "type": "stop",
                "id": message_id,
                "data": references,
                "timestamp": now_unix_milliseconds(),
            }
        )
