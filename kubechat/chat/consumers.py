import json
import logging
import traceback
import config.settings as settings

from channels.generic.websocket import WebsocketConsumer
from kubechat.utils.utils import extract_collection_and_chat_id, now_unix_milliseconds
from langchain.memory import RedisChatMessageHistory


logger = logging.getLogger(__name__)


class EchoConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data, **kwargs):
        self.send(text_data=text_data)


class KubeChatConsumer(WebsocketConsumer):

    def connect(self):
        from kubechat.index import init_index
        from kubechat.models import CollectionType, CollectionStatus
        from kubechat.utils.db import query_collection, query_chat

        user = self.scope["user"]
        collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        collection = query_collection(user, collection_id)
        if collection is None:
            raise Exception("Collection not found")
        if collection.status != CollectionStatus.ACTIVE:
            raise Exception("Collection not active")

        chat = query_chat(user, collection_id, chat_id)
        if chat is None:
            raise Exception("Chat not found")

        self.history = RedisChatMessageHistory(session_id=chat_id, url=settings.MEMORY_REDIS_URL)
        if collection.type == CollectionType.DATABASE:
            pass
        else:
            self.index = init_index(collection_id)

        logger.info(f"Connect to collection: {collection_id}")
        self.accept()

    def disconnect(self, close_code):
        pass

    def predict(self, query):
        prompt = f"""
        Please return a nicely formatted markdown string to this request:

        {query}
        """
        engine = self.index.as_query_engine()
        try:
            result = engine.query(prompt)
        except Exception as e:
            logger.exception(f"Error during query: {e}")
            traceback.print_stack()
            self.send(self.fail_response(str(e)))
            return

        references = result.get_formatted_sources()
        return result.response_txt, references

    def receive(self, text_data, **kwargs):
        data = json.loads(text_data)
        msg_type = data["type"]
        if msg_type == "ping":
            return json.dumps({"type": "pong", "timestamp": now_unix_milliseconds()})

        # save user message to history
        self.history.add_user_message(text_data)

        response_txt, references = self.predict(data["message"])

        response = self.success_response(response_txt, references)

        # save bot message to history
        self.history.add_ai_message(response)

        # response to user
        self.send(response)

    @staticmethod
    def success_response(message, references=None):
        if references is None:
            references = []
        return json.dumps({
            "type": "message",
            "code": "200",
            "data": message,
            "timestamp": now_unix_milliseconds(),
            "references": references,
        })

    @staticmethod
    def fail_response(error):
        return json.dumps({
            "type": "message",
            "data": "",
            "timestamp": now_unix_milliseconds(),
            "code": "500",
            "error": error,
        })


class KubeChatEchoConsumer(KubeChatConsumer):

    def predict(self, query):
        return query, ""
