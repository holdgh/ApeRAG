import json
import logging
import requests

from typing import Optional, List, Mapping, Any
import qdrant_client
from config import settings
from llama_index import ServiceContext
from llama_index import (
    VectorStoreIndex,
)
from langchain.llms.base import LLM
from llama_index.vector_stores.qdrant import QdrantVectorStore

from kubechat.models import Collection, CollectionStatus

logger = logging.getLogger(__name__)


class CustomLLM(LLM):

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        return requests.post(settings.MODEL_SERVER, prompt).text

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"name_of_model": "custom"}

    @property
    def _llm_type(self) -> str:
        return "custom"


def init_index(collection_id: str | int) -> VectorStoreIndex:
    # Retrieve the Collection object
    collection = Collection.objects.get(id=collection_id)
    logger.info(f"init index for collection {collection_id}")

    if collection.status == CollectionStatus.ACTIVE:
        client = qdrant_client.QdrantClient(url=settings.QDRANT_URL)

        service_context = ServiceContext.from_defaults(
            llm=CustomLLM(),
            context_window=2048,
            chunk_size=2048,
            chunk_overlap=200,
        )

        vector_store = QdrantVectorStore(client=client, collection_name=collection.id)
        index = VectorStoreIndex.from_vector_store(
            vector_store, service_context=service_context
        )
        logger.info("Llamaindex loaded and ready for query...")
    else:
        logger.error(f"collection {collection_id} is inactive!")
        raise ValueError("inactive collection")

    return index
