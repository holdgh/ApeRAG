from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from llama_index.vector_stores import qdrant
from llama_index.embeddings import google
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.vector_stores.registry import VECTOR_STORE_TYPE_TO_VECTOR_STORE_CLASS
import qdrant_client
from vectorstore.base import VectorStoreConnector


class QdrantVectorStoreConnector(VectorStoreConnector):
    def __init__(self, ctx: Dict[str, Any], **kwargs: Any) -> None:
        super().__init__(ctx, **kwargs)
        self.ctx = ctx
        self.collection_name = ctx.get("collection", "collection")

        self.url = ctx.get("url", "http://localhost")
        self.port = ctx.get("port", 6333)
        self.grpc_port = ctx.get("grpc_port", 6334)
        self.prefer_grpc = ctx.get("prefer_grpc", False)
        self.https = ctx.get("https", False)
        self.timeout = ctx.get("timeout", 300)
        self.vector_size = ctx.get("vector_size", 1536)

        if self.url == ":memory:":
            self.client = qdrant_client.QdrantClient(":memory:")
        else:
            self.client = qdrant_client.QdrantClient(
                url=self.url,
                port=self.port,
                grpc_port=self.grpc_port,
                prefer_grpc=self.prefer_grpc,
                https=self.https,
                timeout=self.timeout,
                **kwargs,
            )

        self.embedding = ctx.get("embedding", google.GoogleUnivSentEncoderEmbedding)
        self.store = QdrantVectorStore(client=self.client, collection_name=self.collection_name)
