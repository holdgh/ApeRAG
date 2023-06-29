from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from llama_index.vector_stores import qdrant, MilvusVectorStore
from llama_index.embeddings import google
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.vector_stores.registry import VECTOR_STORE_TYPE_TO_VECTOR_STORE_CLASS

from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)
from vectorstore.base import VectorStoreConnector


class MilvusVectorStoreConnector(VectorStoreConnector):
    def __init__(self, ctx: Dict[str, Any], **kwargs: Any) -> None:
        super().__init__(ctx, **kwargs)
        self.ctx = ctx
        self.collection_name = ctx.get("collection", "collection")

        self.host = ctx.get("host", "localhost")
        self.port = ctx.get("port", 19530)
        self.user = ctx.get("user", "")
        self.password = ctx.get("password", "")
        self.alias = f"{self.host}:{self.port}"

        connections.connect(self.alias, host=self.host, port=self.port)
        print("connect successful")

        # be careful that connections is a single instance in pymilvus
        self.client = connections
        self.embedding = ctx.get("embedding", google.GoogleUnivSentEncoderEmbedding)
        self.store = MilvusVectorStore(client=self.client, collection_name=self.collection_name)

    def search(self, **kwargs):
        pass
