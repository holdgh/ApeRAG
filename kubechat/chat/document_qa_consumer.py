import time
import string
import random
import json
import logging
import requests
import config.settings as settings

from channels.generic.websocket import WebsocketConsumer
from kubechat.utils.utils import extract_collection_and_chat_id, now_unix_milliseconds, generate_vector_db_collection_id
from langchain.memory import RedisChatMessageHistory
from langchain.schema import HumanMessage, AIMessage
from vectorstore.connector import VectorStoreConnectorAdaptor
from langchain import PromptTemplate
from query.query import QueryWithEmbedding
from . import embedding_model


logger = logging.getLogger(__name__)

VICUNA_REFINE_TEMPLATE = (
    "### Human:\n"
    "The original question is as follows: {query_str}\n"
    "We have provided an existing answer: {existing_answer}\n"
    "We have the opportunity to refine the existing answer "
    "(only if needed) with some more context below.\n"
    "Given the new context, refine and synthesize the original answer to better \n"
    "answer the question. Make sure that the refine answer is less than 200 words. \n"
    "### Assistant :\n"
)


class DocumentQAConsumer(WebsocketConsumer):

    def connect(self):
        from kubechat.utils.db import query_collection, query_chat

        self.user = self.scope["X-USER-ID"]
        collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        self.collection_id = collection_id
        self.vector_db_collection_id = generate_vector_db_collection_id(self.user, self.collection_id)
        collection = query_collection(self.user, collection_id)
        if collection is None:
            raise Exception("Collection not found")

        chat = query_chat(self.user, collection_id, chat_id)
        if chat is None:
            raise Exception("Chat not found")

        self.history = RedisChatMessageHistory(session_id=chat_id, url=settings.MEMORY_REDIS_URL)

        headers = {"SEC-WEBSOCKET-PROTOCOL": self.scope["Sec-Websocket-Protocol"]}
        self.accept(subprotocol=(None, headers))

    def disconnect(self, close_code):
        pass

    def predict(self, query):
        vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        vectordb_ctx["collection"] = self.vector_db_collection_id
        adaptor = VectorStoreConnectorAdaptor(settings.VECTOR_DB_TYPE, vectordb_ctx)
        vector = embedding_model.get_query_embedding(query)
        query_embedding = QueryWithEmbedding(query=query, top_k=3, embedding=vector)

        results = adaptor.connector.search(
            query_embedding,
            collection_name=self.vector_db_collection_id,
            query_vector=query_embedding.embedding,
            with_vectors=True,
            limit=query_embedding.top_k,
            consistency="majority",
            search_params={"hnsw_ef": 128, "exact": False},
        )

        answer_text = results.get_packed_answer(1900)

        prompt = PromptTemplate.from_template(VICUNA_REFINE_TEMPLATE)
        prompt_str = prompt.format(query_str=query, existing_answer=answer_text)

        input = {
            "prompt": prompt_str,
            "temperature": 0,
            "max_new_tokens": 2048,
            "model": "vicuna-13b",
            "stop": "\nSQLResult:"
        }

        response = requests.post("%s/generate" % settings.MODEL_SERVER, json=input)
        for tokens in response.iter_content():
            yield tokens.decode("ascii")

    def receive(self, text_data, **kwargs):
        data = json.loads(text_data)
        msg_type = data["type"]
        if msg_type == "ping":
            return json.dumps({"type": "pong", "timestamp": now_unix_milliseconds()})

        # save user message to history
        self.history.add_message(HumanMessage(content=text_data, additional_kwargs={"role": "human"}))

        message = ""
        for tokens in self.predict(data["data"]):
            # streaming response to user
            response = self.success_response(tokens, "")
            self.send(text_data=response)

            # concat response tokens
            message += tokens

        # save all tokens as a message to history
        self.history.add_message(AIMessage(content=message, additional_kwargs={"role": "ai"}))


    @staticmethod
    def success_response(message, references=None):
        if references is None:
            references = []
        return json.dumps({
            "type": "message",
            "data": message,
            "timestamp": now_unix_milliseconds(),
            "references": references,
        })

    @staticmethod
    def fail_response(error):
        return json.dumps({
            "type": "error",
            "data": "",
            "timestamp": now_unix_milliseconds(),
            "error": error,
        })

    @staticmethod
    def stop_response():
        return json.dumps({
            "type": "stop",
            "timestamp": now_unix_milliseconds(),
        })


class RandomConsumer(DocumentQAConsumer):
    def connect(self):
        collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        self.history = RedisChatMessageHistory(session_id=chat_id, url=settings.MEMORY_REDIS_URL)
        headers = {"SEC-WEBSOCKET-PROTOCOL": self.scope.get("Sec-Websocket-Protocol")}
        self.accept(subprotocol=(None, headers))

    def disconnect(self, close_code):
        print("disconnect: " + str(close_code))

    def predict(self, query):
        for i in range(0, 100):
            yield ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 10)))
            # mock the thinking time
            time.sleep(random.uniform(0.1, 1))
