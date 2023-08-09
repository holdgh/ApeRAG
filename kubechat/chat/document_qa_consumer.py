import asyncio
import json
import logging

import requests
from langchain import PromptTemplate

import config.settings as settings
from kubechat.utils.utils import generate_vector_db_collection_id
from kubechat.utils.db import query_collection
from query.query import QueryWithEmbedding
from vectorstore.connector import VectorStoreConnectorAdaptor
from typing import Callable, Coroutine, List, Optional, Tuple

from .base_consumer import KUBE_CHAT_DOC_QA_REFERENCES, BaseConsumer

logger = logging.getLogger(__name__)


ENGLISH_PROMPT_TEMPLATE = (
    "### Human:\n"
    "The original question is as follows: {query_str}\n"
    "We have provided an existing answer: {existing_answer}\n"
    "We have the opportunity to refine the existing answer "
    "(only if needed) with some more context below.\n"
    "Given the new context, refine and synthesize the original answer to better \n"
    "answer the question. Please think it step by step and make sure that the refine answer is less than 50 words. \n"
    "### Assistant :\n"
)

CHINESE_PROMPT_TEMPLATE = (
    "### 人类：\n"
    "原问题如下：{query_str}\n"
    "我们已经有了一个答案：{existing_answer}\n"
    "我们有机会完善现有的答案（仅在需要时），下面有更多上下文。\n"
    "根据新提供的上下文信息，优化现有的答案，以便更好的回答问题\n"
    "请一步一步思考，并确保优化后的答案少于 50个字。\n"
    "### 助理："
)

MODEL_PROMPT_TEMPLATES = {
    "vicuna-13b": ENGLISH_PROMPT_TEMPLATE,
    "baichuan-13b": CHINESE_PROMPT_TEMPLATE
}


class DocumentQAConsumer(BaseConsumer):
    async def predict(self, query):
        vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        vector_db_collection_id = generate_vector_db_collection_id(
            self.user, self.collection_id
        )
        vectordb_ctx["collection"] = vector_db_collection_id
        adaptor = VectorStoreConnectorAdaptor(settings.VECTOR_DB_TYPE, vectordb_ctx)
        vector = self.embedding_model.get_text_embedding(query)
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

        answer_text = results.get_packed_answer(1900)

        collection = await query_collection(self.user, self.collection_id)
        config = json.loads(collection.config)
        model = config.get("model", "")

        prompt_template = MODEL_PROMPT_TEMPLATES.get(model, ENGLISH_PROMPT_TEMPLATE)
        prompt = PromptTemplate.from_template(prompt_template)
        prompt_str = prompt.format(query_str=query, existing_answer=answer_text)

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

        references = []
        for result in results.results:
            references.append(
                {
                    "score": result.score,
                    "text": result.text,
                    "metadata": result.metadata,
                }
            )
        yield KUBE_CHAT_DOC_QA_REFERENCES + json.dumps(references)
