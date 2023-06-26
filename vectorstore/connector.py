from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from llama_index.embeddings import base
from llama_index.embeddings import openai
from llama_index.vector_stores.registry import VectorStoreType
from llama_index.vector_stores.registry import VECTOR_STORE_TYPE_TO_VECTOR_STORE_CLASS
from vectorstore.qdrant_connector import QdrantVectorStoreConnector
from vectorstore.base import VectorStoreConnector
import qdrant_client

VECTOR_STORE_TYPE_TO_VECTOR_STORE_CONNECTOR: Dict[VectorStoreType, Type[VectorStoreConnector]] = {
    # VectorStoreType.SIMPLE: SimpleVectorStoreConnector,
    # VectorStoreType.REDIS: RedisVectorStoreConnector,
    # VectorStoreType.WEAVIATE: WeaviateVectorStoreConnector,
    VectorStoreType.QDRANT: QdrantVectorStoreConnector,
    # VectorStoreType.LANCEDB: LanceDBVectorStoreConnector,
    # VectorStoreType.SUPABASE: SupabaseVectorStoreConnector,
    # VectorStoreType.MILVUS: MilvusVectorStoreConnector,
    # VectorStoreType.PINECONE: PineconeVectorStoreConnector,
    # VectorStoreType.OPENSEARCH: OpensearchVectorStoreConnector,
    # VectorStoreType.FAISS: FaissVectorStoreConnector,
    # VectorStoreType.CHROMA: ChromaVectorStoreConnector,
    # VectorStoreType.CHATGPT_PLUGIN: ChatGPTRetrievalPluginClientConnector,
    # VectorStoreType.DEEPLAKE: DeepLakeVectorStoreConnector,
    # VectorStoreType.MYSCALE: MyScaleVectorStoreConnector,
}


class VectorStoreConnectorAdaptor:
    def __init__(self, vector_store_type, ctx: Dict[str, Any], **kwargs: Any) -> None:
        self.ctx = ctx
        self.vector_store_type = vector_store_type

        vector_store_class = VECTOR_STORE_TYPE_TO_VECTOR_STORE_CLASS[vector_store_type]
        if vector_store_class is None:
            raise ValueError("unsupported vector store type:", vector_store_type)

        typed_connector = VECTOR_STORE_TYPE_TO_VECTOR_STORE_CONNECTOR[vector_store_type]
        self.connector = typed_connector(ctx, **kwargs)
