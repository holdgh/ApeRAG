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
from .prompts import DEFAULT_MODEL_PROMPT_TEMPLATES, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2

logger = logging.getLogger(__name__)


class DocumentQAConsumer(BaseConsumer):
    async def predict(self, query):
        collection_config = json.loads(self.collection.config)

        vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        vector_db_collection_id = generate_vector_db_collection_id(
            self.user, self.collection_id
        )
        vectordb_ctx["collection"] = vector_db_collection_id
        adaptor = VectorStoreConnectorAdaptor(settings.VECTOR_DB_TYPE, vectordb_ctx)
        vector = self.embedding_model.get_text_embedding(query)

        llm_config = collection_config.get("llm", {})
        score_threshold = llm_config.get("similarity_score_threshold", 0.5)
        topk = llm_config.get("similarity_topk", 3)
        context_window = llm_config.get("context_window", 1900)

        query_embedding = QueryWithEmbedding(query=query, top_k=topk, embedding=vector)
        results = adaptor.connector.search(
            query_embedding,
            collection_name=vector_db_collection_id,
            query_vector=query_embedding.embedding,
            with_vectors=True,
            limit=query_embedding.top_k,
            consistency="majority",
            search_params={"hnsw_ef": 128, "exact": False},
            score_threshold=score_threshold,
        )
        query_context = results.get_packed_answer(context_window)

        model = collection_config.get("model", "")
        prompt_template = collection_config.get("prompt_template", None)
        if not prompt_template:
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
