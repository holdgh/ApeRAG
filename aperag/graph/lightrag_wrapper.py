import asyncio
import logging
from typing import Optional, List, Any, Dict, Callable, Awaitable

import numpy
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm.openai import openai_embed, openai_complete_if_cache
from lightrag.kg.shared_storage import initialize_pipeline_status

from aperag.utils.utils import generate_lightrag_namespace_prefix
from config.settings import (
    LIGHT_RAG_LLM_API_KEY,
    LIGHT_RAG_LLM_BASE_URL,
    LIGHT_RAG_LLM_MODEL,
    LIGHT_RAG_EMBEDDING_API_KEY,
    LIGHT_RAG_EMBEDDING_BASE_URL,
    LIGHT_RAG_EMBEDDING_MODEL,
    LIGHT_RAG_EMBEDDING_DIM,
    LIGHT_RAG_EMBEDDING_MAX_TOKENS,
    LIGHT_RAG_WORKING_DIR,
    LIGHT_RAG_ENABLE_LLM_CACHE,
    LIGHT_RAG_MAX_PARALLEL_INSERT,
)

# --- Configuration Parameters---
LLM_API_KEY = LIGHT_RAG_LLM_API_KEY
LLM_BASE_URL = LIGHT_RAG_LLM_BASE_URL
LLM_MODEL = LIGHT_RAG_LLM_MODEL
EMBEDDING_MODEL = LIGHT_RAG_EMBEDDING_MODEL
EMBEDDING_API_KEY = LIGHT_RAG_EMBEDDING_API_KEY
EMBEDDING_BASE_URL = LIGHT_RAG_EMBEDDING_BASE_URL
EMBEDDING_DIM = LIGHT_RAG_EMBEDDING_DIM
EMBEDDING_MAX_TOKENS = LIGHT_RAG_EMBEDDING_MAX_TOKENS
WORKING_DIR = LIGHT_RAG_WORKING_DIR
ENABLE_LLM_CACHE = LIGHT_RAG_ENABLE_LLM_CACHE
MAX_PARALLEL_INSERT = LIGHT_RAG_MAX_PARALLEL_INSERT
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

    async def query(self, query: str, param: QueryParam) -> Any:
        return await self.rag.aquery(query, param=param)


# ---------- Default llm_func & embed_impl ---------- #
async def _default_llm_func(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: List = [],
    **kwargs,
) -> str:
    merged_kwargs = {
        "api_key": LLM_API_KEY,
        "base_url": LLM_BASE_URL,
        "model": LLM_MODEL,
        **kwargs,
    }
    return await openai_complete_if_cache(
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        **merged_kwargs,
    )


async def _default_embed_impl(texts: List[str]) -> numpy.ndarray:
    return await openai_embed(
        texts,
        model=EMBEDDING_MODEL,
        api_key=EMBEDDING_API_KEY,
        base_url=EMBEDDING_BASE_URL,
    )


# Module-level cache
_lightrag_instances: Dict[str, LightRagHolder] = {}
_initialization_lock = asyncio.Lock()


async def _create_and_initialize_lightrag(
    namespace_prefix: str,
    llm_func: Callable[..., Awaitable[str]],
    embed_impl: Callable[[List[str]], Awaitable[numpy.ndarray]],
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
    logger.debug(f"Creating and initializing LightRAG object for namespace: '{namespace_prefix}'...")

    rag = LightRAG(
        namespace_prefix=namespace_prefix,
        working_dir=WORKING_DIR,
        llm_model_func=llm_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=EMBEDDING_DIM,
            max_token_size=EMBEDDING_MAX_TOKENS,
            func=embed_impl,
        ),
        enable_llm_cache=ENABLE_LLM_CACHE,
        max_parallel_insert=MAX_PARALLEL_INSERT,
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    logger.debug(f"LightRAG object for namespace '{namespace_prefix}' fully initialized.")
    return LightRagHolder(rag=rag, llm_func=llm_func, embed_impl=embed_impl)


async def get_lightrag_instance(
    collection,
    llm_func: Callable[..., Awaitable[str]] = _default_llm_func,
    embed_impl: Callable[[List[str]], Awaitable[numpy.ndarray]] = _default_embed_impl,
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
            client = await _create_and_initialize_lightrag(namespace_prefix, llm_func, embed_impl)
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


async def query_lightrag(query: str, param: QueryParam, collection) -> Optional[Any]:
    try:
        client = await get_lightrag_instance(collection=collection)
        return await client.query(query, param=param)
    except (RuntimeError, ValueError) as e:
        logger.error(f"Cannot query LightRAG for collection '{collection.id}': {e}")
        return None
    except Exception as e:
        logger.exception(
            f"Error during LightRAG query for collection '{collection.id}', query '{query[:50]}...'", exc_info=e
        )
        return None