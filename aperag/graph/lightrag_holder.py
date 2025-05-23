import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Callable, Awaitable, Tuple, AsyncIterator, Any

import json
import numpy
from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.openai import openai_complete_if_cache
from lightrag.utils import EmbeddingFunc
from lightrag.base import DocStatus

from aperag.db.models import Collection
from aperag.db.ops import (
    query_msp_dict,
)
from aperag.embed.base_embedding import get_collection_embedding_service
from aperag.schema.utils import parseCollectionConfig
from aperag.utils.utils import generate_lightrag_namespace_prefix
from config.settings import (
    LIGHT_RAG_LLM_API_KEY,
    LIGHT_RAG_LLM_BASE_URL,
    LIGHT_RAG_LLM_MODEL,
    LIGHT_RAG_WORKING_DIR,
    LIGHT_RAG_ENABLE_LLM_CACHE,
    LIGHT_RAG_MAX_PARALLEL_INSERT,
)

# --- Configuration Parameters---
LLM_API_KEY = LIGHT_RAG_LLM_API_KEY
LLM_BASE_URL = LIGHT_RAG_LLM_BASE_URL
LLM_MODEL = LIGHT_RAG_LLM_MODEL
WORKING_DIR = LIGHT_RAG_WORKING_DIR
ENABLE_LLM_CACHE = LIGHT_RAG_ENABLE_LLM_CACHE
MAX_PARALLEL_INSERT = LIGHT_RAG_MAX_PARALLEL_INSERT
LLM_MODEL_MAX_ASYNC = 20
ENTITY_EXTRACT_MAX_GLEANING = 0
# --- End Configuration Parameters ---

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class LightRagHolder:
    """
    Wrapper class holding a LightRAG instance and its llm / embedding implementations.
    """

    def __init__(
        self,
        rag: LightRAG,
        llm_func: Callable[..., Awaitable[str]],
        embed_impl: Callable[[List[str]], Awaitable[numpy.ndarray]],
    ) -> None:
        self.rag = rag
        self.llm_func = llm_func
        self.embed_impl = embed_impl

    async def ainsert(
            self,
            input: str | list[str],
            split_by_character: str | None = None,
            split_by_character_only: bool = False,
            ids: str | list[str] | None = None,
            file_paths: str | list[str] | None = None,
    ) -> None:
        return await self.rag.ainsert(input, split_by_character, split_by_character_only, ids, file_paths)

    async def get_processed_docs(self) -> dict[str, Any]:
        return await self.rag.get_docs_by_status(DocStatus.PROCESSED)

    async def aget_docs_by_ids(self, ids: str | list[str]) -> dict[str, Any]:
        return await self.rag.aget_docs_by_ids(ids)

    async def aquery(self, query: str, param: QueryParam = QueryParam(), system_prompt: str | None = None) -> str | AsyncIterator[str]:
        return await self.rag.aquery(query, param, system_prompt)

    async def adelete_by_doc_id(self, doc_id: str) -> None:
        return await self.rag.adelete_by_doc_id(doc_id)


async def gen_lightrag_llm_func(collection: Collection) -> Callable[..., Awaitable[str]]:
    config = parseCollectionConfig(collection.config)

    lightrag_msp = config.completion.model_service_provider
    lightrag_model_name = config.completion.model
    logging.info("gen_lightrag_llm_func %s %s", lightrag_msp, lightrag_model_name)

    msp_dict = await query_msp_dict(collection.user)
    if lightrag_msp in msp_dict:
        msp = msp_dict[lightrag_msp]
        base_url = msp.base_url
        api_key = msp.api_key
        logging.info("gen_lightrag_llm_func %s %s", base_url, api_key)

        async def lightrag_llm_func(
                prompt: str,
                system_prompt: Optional[str] = None,
                history_messages: List = [],
                **kwargs,
        ) -> str:
            start_time = datetime.now()
            merged_kwargs = {
                "api_key": api_key,
                "base_url": base_url,
                **config.completion.dict()
            }

            from aperag.llm.completion_service import CompletionService
            completion_service = CompletionService(**merged_kwargs)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if history_messages:
                messages.extend(history_messages)

            # 使用 CompletionService 的公共 agenerate_stream 方法
            full_response = ""
            async for chunk in completion_service.agenerate_stream(
                    history=messages,
                    prompt=prompt,
                    memory=True if messages else False
            ):
                if chunk:
                    full_response += chunk

            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() if start_time and end_time else 0.0
            logger.info(f"LLM Start Time: {start_time}")
            logger.info(f"LLM End Time: {end_time}")
            logger.info(f"LLM Latency: {latency:.2f} seconds")
            logger.info(f"LLM PROMPT: {prompt}")
            logger.info(f"LLM RESPONSE: {full_response}")
            return full_response

        return lightrag_llm_func

    return None

# Module-level cache
_lightrag_instances: Dict[str, LightRagHolder] = {}
_initialization_lock = asyncio.Lock()


async def _create_and_initialize_lightrag(
    namespace_prefix: str,
    llm_func: Callable[..., Awaitable[str]],
    embed_impl: Callable[[List[str]], Awaitable[numpy.ndarray]],
    embed_dim: int
) -> LightRagHolder:
    """
    Creates the LightRAG dependencies, instantiates the object for a specific namespace,
    and runs its asynchronous initializers using supplied callable implementations.
    Returns a fully ready LightRagClient for the given namespace.

    Args:
        namespace_prefix: The namespace prefix for this LightRAG instance.
        llm_func: Async callable that produces LLM completions.
        embed_impl: Async callable that produces embeddings.
    """
    logger.info(f"Creating and initializing LightRAG object for namespace: '{namespace_prefix}'...")

    # POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
    # POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
    # POSTGRES_USER = os.environ.get("POSTGRES_USER")
    # POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
    # POSTGRES_DATABASE = os.environ.get("POSTGRES_DB")
    # POSTGRES_WORKSPACE = namespace_prefix
    # os.environ["POSTGRES_DATABASE"] = POSTGRES_DATABASE
    # os.environ["POSTGRES_WORKSPACE"] = POSTGRES_WORKSPACE
    #
    # logger.info(f"LightRAG env: POSTGRES_HOST='{POSTGRES_HOST}'...")
    # logger.info(f"LightRAG env: POSTGRES_PORT='{POSTGRES_PORT}'...")
    # logger.info(f"LightRAG env: POSTGRES_USER='{POSTGRES_USER}'...")
    # logger.info(f"LightRAG env: POSTGRES_PASSWORD='{POSTGRES_PASSWORD}'...")
    # logger.info(f"LightRAG env: POSTGRES_DATABASE='{POSTGRES_DATABASE}'...")
    # logger.info(f"LightRAG env: POSTGRES_WORKSPACE='{POSTGRES_WORKSPACE}'...")

    rag = LightRAG(
        namespace_prefix=namespace_prefix,
        working_dir=WORKING_DIR,
        llm_model_func=llm_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=embed_dim,
            max_token_size=8192,
            func=embed_impl,
        ),
        enable_llm_cache=ENABLE_LLM_CACHE,
        max_parallel_insert=MAX_PARALLEL_INSERT,
        llm_model_max_async=LLM_MODEL_MAX_ASYNC,
        entity_extract_max_gleaning=ENTITY_EXTRACT_MAX_GLEANING,
        # kv_storage="PGKVStorage",
        # vector_storage="PGVectorStorage",
        # graph_storage="PGGraphStorage",
        # doc_status_storage="PGDocStatusStorage",
        addon_params={
            "language": "Simplified Chinese",
            # "language": "English",
        },
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    logger.debug(f"LightRAG object for namespace '{namespace_prefix}' fully initialized.")
    return LightRagHolder(rag=rag, llm_func=llm_func, embed_impl=embed_impl)


async def gen_lightrag_embed_func(collection: Collection) -> Tuple[
    Callable[[list[str]], Awaitable[numpy.ndarray]],
    int
]:
    embedding_svc, dim = await get_collection_embedding_service(collection)
    async def lightrag_embed_func(texts: list[str]) -> numpy.ndarray:
        embeddings = await embedding_svc.aembed_documents(texts)
        return numpy.array(embeddings)

    return lightrag_embed_func, dim


async def get_lightrag_holder(
    collection: Collection
) -> LightRagHolder:
    namespace_prefix: str = generate_lightrag_namespace_prefix(collection.id)
    if not namespace_prefix or not isinstance(namespace_prefix, str):
        raise ValueError("A valid namespace_prefix string must be provided.")

    if namespace_prefix in _lightrag_instances:
        return _lightrag_instances[namespace_prefix]

    async with _initialization_lock:
        if namespace_prefix in _lightrag_instances:
            return _lightrag_instances[namespace_prefix]

        logger.info(f"Initializing LightRAG instance for namespace '{namespace_prefix}' (lazy loading)...")
        try:
            embed_func, dim = await gen_lightrag_embed_func(collection=collection)
            llm_func = await gen_lightrag_llm_func(collection=collection)
            client = await _create_and_initialize_lightrag(namespace_prefix, llm_func, embed_func, embed_dim=dim)
            _lightrag_instances[namespace_prefix] = client
            logger.info(f"LightRAG instance for namespace '{namespace_prefix}' initialized successfully.")
            return client
        except Exception as e:
            logger.exception(
                f"Failed during LightRAG instance creation/initialization for namespace '{namespace_prefix}'.",
                exc_info=e,
            )
            _lightrag_instances.pop(namespace_prefix, None)
            raise RuntimeError(
                f"Failed during LightRAG instance creation/initialization for namespace '{namespace_prefix}'"
            ) from e


async def reload_lightrag_holder(collection: Collection):
    delete_lightrag_holder(collection)
    await get_lightrag_holder(collection)


async def delete_lightrag_holder(collection: Collection):
    namespace_prefix: str = generate_lightrag_namespace_prefix(collection.id)
    if not namespace_prefix or not isinstance(namespace_prefix, str):
        return
    async with _initialization_lock:
        if namespace_prefix in _lightrag_instances:
            logger.info(f"Removing existing LightRAG instance for namespace '{namespace_prefix}' for reload...")
            del _lightrag_instances[namespace_prefix]