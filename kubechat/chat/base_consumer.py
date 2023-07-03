import datetime
import json
import logging
from abc import abstractmethod

from channels.generic.websocket import WebsocketConsumer
from langchain.memory import RedisChatMessageHistory
from langchain.schema import HumanMessage, AIMessage, BaseChatMessageHistory
from readers.base_embedding import get_default_embedding_model

import config.settings as settings
from kubechat.utils.utils import extract_collection_and_chat_id, now_unix_milliseconds
from kubechat.auth.validator import DEFAULT_USER

logger = logging.getLogger(__name__)


KUBE_CHAT_DOC_QA_REFERENCES = "|KUBE_CHAT_DOC_QA_REFERENCES|"


class BaseConsumer(WebsocketConsumer):

    def __init__(self):
        super().__init__()
        self.collection_id = None
        self.embedding_model = None
        self.vector_size = 0
        self.history = None
        self.user = DEFAULT_USER

    def connect(self):
        from kubechat.utils.db import query_collection, query_chat

        self.user = self.scope["X-USER-ID"]
        collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        self.collection_id = collection_id
        collection = query_collection(self.user, collection_id)
        if collection is None:
            raise Exception("Collection not found")

        chat = query_chat(self.user, collection_id, chat_id)
        if chat is None:
            raise Exception("Chat not found")

        self.embedding_model, self.vector_size = get_default_embedding_model()

        self.history = RedisChatMessageHistory(session_id=chat_id, url=settings.MEMORY_REDIS_URL)

        headers = {}
        token = self.scope.get("Sec-Websocket-Protocol", None)
        if token is not None:
            headers = {"SEC-WEBSOCKET-PROTOCOL": token}
        self.accept(subprotocol=(None, headers))

    def disconnect(self, close_code):
        pass

    @abstractmethod
    def predict(self, query):
        pass

    def receive(self, text_data, **kwargs):
        data = json.loads(text_data)
        self.msg_type = data["type"]
        self.response_type = "message"

        # save user message to history
        if self.msg_type != "sql":
            self.history.add_message(HumanMessage(content=text_data, additional_kwargs={"role": "human"}))

        message = ""
        message_id = f'{now_unix_milliseconds()}'

        # send start message
        self.send(text_data=self.start_response(message_id))

        references = []
        for tokens in self.predict(data["data"]):
            if tokens.startswith(KUBE_CHAT_DOC_QA_REFERENCES):
                references = json.loads(tokens[len(KUBE_CHAT_DOC_QA_REFERENCES):])
                continue

            # streaming response
            response = self.success_response(message_id, tokens, issql=self.response_type == "sql")
            self.send(text_data=response)

            # concat response tokens
            message += tokens

        # send stop message
        self.send(text_data=self.stop_response(message_id, references))

        # save all tokens as a message to history
        self.history.add_message(
            AIMessage(
                content=self.success_response(
                    message_id,
                    message,
                    issql=self.response_type == "sql"
                ),
                additional_kwargs={"role": "ai", "references": references}
            )
        )

    @staticmethod
    def success_response(message_id, data, issql=False):
        return json.dumps({
            "type": "message" if not issql else "sql",
            "id": message_id,
            "data": data,
            "timestamp": now_unix_milliseconds(),
        })

    @staticmethod
    def fail_response(message_id, error):
        return json.dumps({
            "type": "error",
            "id": message_id,
            "data": error,
            "timestamp": now_unix_milliseconds(),
        })

    @staticmethod
    def start_response(message_id):
        return json.dumps({
            "type": "start",
            "id": message_id,
            "timestamp": now_unix_milliseconds(),
        })

    @staticmethod
    def stop_response(message_id, references):
        if references is None:
            references = []
        return json.dumps({
            "type": "stop",
            "id": message_id,
            "data": references,
            "timestamp": now_unix_milliseconds(),
        })
