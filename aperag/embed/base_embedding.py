#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any
import logging

from langchain_core.embeddings import Embeddings

from aperag.embed.embedding_service import EmbeddingService

from aperag.db.ops import (
    query_msp_dict,
)

from aperag.vectorstore.connector import VectorStoreConnectorAdaptor
from config.settings import (
    EMBEDDING_MAX_CHUNKS_IN_BATCH,
)

mutex = Lock()

def synchronized(func):
    def wrapper(*args, **kwargs):
        with mutex:
            return func(*args, **kwargs)

    return wrapper

# TODO: delete this function
def loads_or_use_default_embedding_configs(config):
    """
    Load embedding configurations from the provided config dict,
    or use default values from settings if not present.

    Args:
        config (dict): The configuration dictionary to load from

    Returns:
        dict: The updated configuration dictionary with all embedding settings
    """
    config["embedding_backend"] = config.get("embedding_backend", EMBEDDING_BACKEND)
    config["embedding_model"] = config.get("embedding_model", EMBEDDING_MODEL)
    config["embedding_dim"] = config.get("embedding_dim", EMBEDDING_DIM)
    config["embedding_service_url"] = config.get("embedding_service_url", EMBEDDING_SERVICE_URL)
    config["embedding_service_api_key"] = config.get("embedding_service_api_key", EMBEDDING_SERVICE_API_KEY)
    config["embedding_max_chunks_in_batch"] = config.get("embedding_max_chunks_in_batch", EMBEDDING_MAX_CHUNKS_IN_BATCH)
    return config


_dimension_cache: dict[tuple[str, str], int] = {}


def _get_embedding_dimension(embedding_svc: EmbeddingService, embedding_backend: str, embedding_model) -> int:
    cache_key = (embedding_backend, embedding_model)
    if cache_key in _dimension_cache:
        return _dimension_cache[cache_key]
    vec = embedding_svc.embed_query("dimension_probe")
    if not vec:
        raise RuntimeError("Failed to obtain embedding vector while probing dimension.")
    if isinstance(vec[0], (list, tuple)):
        vec = vec[0]
    dim = len(vec)
    _dimension_cache[cache_key] = dim
    return dim


@synchronized
def get_embedding_model(
        embedding_backend: str,
        embedding_model: str,
        embedding_service_url: str,
        embedding_service_api_key: str,
        embedding_max_chunks_in_batch: int = EMBEDDING_MAX_CHUNKS_IN_BATCH,
        **kwargs) -> tuple[Embeddings | None, int]:
    embedding_svc = EmbeddingService(embedding_backend, embedding_model,
                                     embedding_service_url, embedding_service_api_key, embedding_max_chunks_in_batch)
    embedding_dim = _get_embedding_dimension(embedding_svc, embedding_backend, embedding_model)
    return embedding_svc, embedding_dim


async def get_collection_embedding_model(collection) -> tuple[Embeddings | None, int]:
    config = json.loads(collection.config)
    embedding_backend = config.get("embedding_model_service_provider", "")
    embedding_model_name = config.get("embedding_model_name", "")
    logging.info("get_collection_embedding_model %s %s", embedding_backend, embedding_model_name)

    msp_dict = await query_msp_dict(collection.user)
    if embedding_backend in msp_dict:
        msp = msp_dict[embedding_backend]
        embedding_service_url = msp.base_url
        embedding_service_api_key = msp.api_key
        logging.info("get_collection_embedding_model %s %s", embedding_service_url, embedding_service_api_key)

        return get_embedding_model(
            embedding_backend=embedding_backend,
            embedding_model=embedding_model_name,
            embedding_service_url=embedding_service_url,
            embedding_service_api_key=embedding_service_api_key,
            embedding_max_chunks_in_batch=EMBEDDING_MAX_CHUNKS_IN_BATCH,
        )
    
    logging.warning("get_collection_embedding_model cannot find model service provider %s", embedding_backend)
    return None, 0


class DocumentBaseEmbedding(ABC):
    def __init__(
            self,
            vector_store_adaptor: VectorStoreConnectorAdaptor,
            embedding_model: Embeddings = None,
            vector_size: int = None,
            **kwargs: Any,
    ) -> None:
        self.connector = vector_store_adaptor.connector
        # Improved logic to handle optional embedding_model/vector_size
        if embedding_model is None or vector_size is None:
            raise ValueError("lacks embedding model or vector size")
        
        self.embedding, self.vector_size = embedding_model, vector_size
        self.client = vector_store_adaptor.connector.client

    @abstractmethod
    def load_data(self, **kwargs: Any):
        pass