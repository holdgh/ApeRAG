import json
import logging

import requests
from langchain import PromptTemplate

import config.settings as settings
from kubechat.utils.utils import generate_vector_db_collection_id
from query.query import QueryWithEmbedding
from vectorstore.connector import VectorStoreConnectorAdaptor

from .base_consumer import KUBE_CHAT_DOC_QA_REFERENCES, BaseConsumer

logger = logging.getLogger(__name__)

VICUNA_REFINE_TEMPLATE = (
    "### Human:\n"
    "The original question is as follows: {query_str}\n"
    "We have provided an existing answer: {existing_answer}\n"
    "We have the opportunity to refine the existing answer "
    "(only if needed) with some more context below.\n"
    "Given the new context, refine and synthesize the original answer to better \n"
    "answer the question. Make sure that the refine answer is less than 50 words. \n"
    "### Assistant :\n"
)


class DocumentQAConsumer(BaseConsumer):
    def predict(self, query):
        vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        vector_db_collection_id = generate_vector_db_collection_id(
            self.user, self.collection_id
        )
        vectordb_ctx["collection"] = vector_db_collection_id
        adaptor = VectorStoreConnectorAdaptor(settings.VECTOR_DB_TYPE, vectordb_ctx)
        vector = self.embedding_model.get_query_embedding(query)
        query_embedding = QueryWithEmbedding(query=query, top_k=3, embedding=vector)

        results = adaptor.connector.search(
            query_embedding,
            collection_name=vector_db_collection_id,
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
            "stop": "\nSQLResult:",
        }

        response = requests.post(
            "%s/generate_stream" % settings.MODEL_SERVER, json=input, stream=True,
        )
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
                buffer = buffer[idx + 1 :]

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
