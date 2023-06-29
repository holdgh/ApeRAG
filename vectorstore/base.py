from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from llama_index.vector_stores.types import VectorStore
from llama_index.embeddings.base import BaseEmbedding


class VectorStoreConnector(ABC):
    def __init__(self, ctx: Dict[str, Any], **kwargs: Any) -> None:
        self.ctx = ctx
        self.client = None
        self.embedding : BaseEmbedding = None
        self.store : VectorStore = None

    @abstractmethod
    def search(self, **kwargs):
        pass