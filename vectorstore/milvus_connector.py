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

        self.url = ctx.get("url", "http://localhost")
        self.port = ctx.get("port", 19530)
        self.grpc_port = ctx.get("grpc_port", 6334)
        self.prefer_grpc = ctx.get("prefer_grpc", False)
        self.https = ctx.get("https", False)
        self.timeout = ctx.get("timeout", 300)
        self.vector_size = ctx.get("vector_size", 1536)

        self.client = connections.connect("default", host="localhost", port="19530")
        print("connect successful")
        self.embedding = ctx.get("embedding", google.GoogleUnivSentEncoderEmbedding)
        self.store = MilvusVectorStore(client=self.client, collection_name=self.collection_name)
