from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client
from qdrant_client.models import Distance,VectorParams
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
        self.distance = ctx.get("distance", "Cosine")

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

        self.store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=self.distance))
