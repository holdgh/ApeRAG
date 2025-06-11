# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional, Tuple

import numpy

from aperag.concurrent_control import get_or_create_lock
from aperag.db.models import Collection
from aperag.db.ops import (
    db_ops,
)
from aperag.embed.base_embedding import get_collection_embedding_service
from aperag.graph.lightrag import LightRAG, QueryParam
from aperag.graph.lightrag.base import DocStatus
from aperag.graph.lightrag.utils import EmbeddingFunc
from aperag.schema.utils import parseCollectionConfig

logger = logging.getLogger(__name__)


# Configuration constants
class LightRAGConfig:
    """Centralized configuration for LightRAG"""

    # Storage Configuration
    WORKING_DIR = "./documents"

    # Chunking Configuration
    CHUNK_TOKEN_SIZE = 3000
    CHUNK_OVERLAP_TOKEN_SIZE = 100

    # Performance Configuration
    MAX_PARALLEL_INSERT = 2
    LLM_MODEL_MAX_ASYNC = 20
    ENTITY_EXTRACT_MAX_GLEANING = 0
    EMBEDDING_MAX_TOKEN_SIZE = 8192

    # Logging Configuration
    DEFAULT_LANGUAGE = "Simplified Chinese"


class LightRAGError(Exception):
    """Base exception for LightRAG operations"""

    pass


class LightRAGInitializationError(LightRAGError):
    """Exception raised during LightRAG initialization"""

    pass


class LightRAGServiceError(LightRAGError):
    """Exception raised during LightRAG service operations"""

    pass


class LightRagHolder:
    """Wrapper for LightRAG instance with lifecycle management and error handling"""

    def __init__(
        self,
        rag: LightRAG,
        llm_func: Callable[..., Awaitable[str]],
        embed_impl: Callable[[List[str]], Awaitable[numpy.ndarray]],
        collection_id: str,
    ) -> None:
        """Initialize with LightRAG instance and related functions"""
        self.rag = rag
        self.llm_func = llm_func
        self.embed_impl = embed_impl
        self.collection_id = collection_id
        self._creation_time = datetime.now()
        logger.info(f"LightRagHolder created for collection: {collection_id}")

    @property
    def creation_time(self) -> datetime:
        """Get the creation time of this holder"""
        return self._creation_time

    async def ainsert(
        self,
        input: str | list[str],
        split_by_character: str | None = None,
        split_by_character_only: bool = False,
        ids: str | list[str] | None = None,
        file_paths: str | list[str] | None = None,
    ) -> None:
        """Insert documents with error handling"""
        try:
            logger.info(f"Inserting documents into LightRAG collection: {self.collection_id}")
            return await self.rag.ainsert(input, split_by_character, split_by_character_only, ids, file_paths)
        except Exception as e:
            logger.error(f"Failed to insert documents into LightRAG collection {self.collection_id}: {str(e)}")
            raise LightRAGServiceError(f"Document insertion failed: {str(e)}") from e

    async def get_processed_docs(self) -> dict[str, Any]:
        """Get processed documents with error handling"""
        try:
            return await self.rag.get_docs_by_status(DocStatus.PROCESSED)
        except Exception as e:
            logger.error(f"Failed to get processed docs from LightRAG collection {self.collection_id}: {str(e)}")
            raise LightRAGServiceError(f"Failed to get processed docs: {str(e)}") from e

    async def aget_docs_by_ids(self, ids: str | list[str]) -> dict[str, Any]:
        """Get documents by IDs with error handling"""
        try:
            return await self.rag.aget_docs_by_ids(ids)
        except Exception as e:
            logger.error(f"Failed to get docs by IDs from LightRAG collection {self.collection_id}: {str(e)}")
            raise LightRAGServiceError(f"Failed to get docs by IDs: {str(e)}") from e

    async def aquery(
        self, query: str, param: QueryParam = QueryParam(), system_prompt: str | None = None
    ) -> str | AsyncIterator[str]:
        """Query LightRAG with error handling"""
        try:
            logger.info(f"Querying LightRAG collection {self.collection_id} with query: {query[:100]}...")
            return await self.rag.aquery(query, param, system_prompt)
        except Exception as e:
            logger.error(f"Failed to query LightRAG collection {self.collection_id}: {str(e)}")
            raise LightRAGServiceError(f"Query failed: {str(e)}") from e

    async def adelete_by_doc_id(self, doc_id: str) -> None:
        """Delete document by ID with error handling"""
        try:
            logger.info(f"Deleting document {doc_id} from LightRAG collection: {self.collection_id}")
            return await self.rag.adelete_by_doc_id(doc_id)
        except Exception as e:
            logger.error(
                f"Failed to delete document {doc_id} from LightRAG collection {self.collection_id}: {str(e)}"
            )
            raise LightRAGServiceError(f"Document deletion failed: {str(e)}") from e

    async def adelete_by_collection(self, collection_id: str) -> None:
        """Delete all documents for a collection with error handling"""
        try:
            logger.info(
                f"Deleting all documents for collection {collection_id} from LightRAG collection: {self.collection_id}"
            )

            # Get all document IDs in this collection
            document_ids = db_ops.query_documents(collection_id).values_list("id", flat=True)
            document_ids = [str(doc_id) async for doc_id in document_ids]

            if not document_ids:
                logger.info(f"No documents found for collection {collection_id}, skipping deletion")
                return

            # Delete each document from lightrag
            deleted_count = 0
            failed_count = 0
            for document_id in document_ids:
                try:
                    await self.rag.adelete_by_doc_id(document_id)
                    deleted_count += 1
                    logger.debug(f"Successfully deleted lightrag document for document ID: {document_id}")
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"Failed to delete lightrag document for document ID {document_id}: {str(e)}")

            logger.info(
                f"Completed lightrag document deletion for collection {collection_id}: {deleted_count} deleted, {failed_count} failed"
            )

        except Exception as e:
            # Log error but don't raise - let the deletion task continue with other cleanup
            logger.error(f"Error during lightrag collection deletion for collection {collection_id}: {str(e)}")
            logger.warning("Continuing with other cleanup tasks despite lightrag deletion failure")


def log_llm_performance(start_time: datetime, end_time: datetime, prompt: str, response: str) -> None:
    """Log LLM performance metrics"""
    latency = (end_time - start_time).total_seconds() if start_time and end_time else 0.0
    logger.info(f"LLM Performance - Start: {start_time}, End: {end_time}, Latency: {latency:.2f}s")
    logger.debug(f"LLM PROMPT: {prompt[:200]}..." if len(prompt) > 200 else f"LLM PROMPT: {prompt}")
    logger.debug(f"LLM RESPONSE: {response[:200]}..." if len(response) > 200 else f"LLM RESPONSE: {response}")


async def create_lightrag_llm_func(collection: Collection, msp_dict: Dict[str, Any]) -> Callable[..., Awaitable[str]]:
    """Create LightRAG LLM function with proper error handling"""
    config = parseCollectionConfig(collection.config)
    lightrag_msp = config.completion.model_service_provider
    lightrag_model_name = config.completion.model

    logger.info(f"Creating LightRAG LLM function with MSP: {lightrag_msp}, Model: {lightrag_model_name}")

    if lightrag_msp not in msp_dict:
        raise LightRAGInitializationError(
            f"Model service provider '{lightrag_msp}' not found in user's MSP configuration"
        )

    msp = msp_dict[lightrag_msp]
    api_key = msp.api_key

    # Get base_url from LLMProvider
    try:
        from aperag.db.models import LLMProvider

        llm_provider = db_ops.query_llm_provider_by_name(lightrag_msp)
        base_url = llm_provider.base_url
    except LLMProvider.DoesNotExist:
        raise LightRAGInitializationError(f"LLMProvider '{lightrag_msp}' not found")

    logger.info(f"Using base URL: {base_url}")

    async def lightrag_llm_func(
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: List = [],
        **kwargs,
    ) -> str:
        start_time = datetime.now()

        try:
            merged_kwargs = {"api_key": api_key, "base_url": base_url, **config.completion.dict()}

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
                history=messages, prompt=prompt, memory=True if messages else False
            ):
                if chunk:
                    full_response += chunk

            end_time = datetime.now()
            log_llm_performance(start_time, end_time, prompt, full_response)
            return full_response

        except Exception as e:
            end_time = datetime.now()
            logger.error(f"LLM function failed after {(end_time - start_time).total_seconds():.2f}s: {str(e)}")
            raise LightRAGServiceError(f"LLM completion failed: {str(e)}") from e

    return lightrag_llm_func


async def gen_lightrag_llm_func(collection: Collection) -> Callable[..., Awaitable[str]]:
    """Generate LightRAG LLM function with improved error handling"""
    try:
        msp_dict = db_ops.query_msp_dict(collection.user)
        return await create_lightrag_llm_func(collection, msp_dict)
    except Exception as e:
        logger.error(f"Failed to generate LightRAG LLM function for collection {collection.id}: {str(e)}")
        raise LightRAGInitializationError(f"Failed to create LLM function: {str(e)}") from e


async def gen_lightrag_embed_func(
    collection: Collection,
) -> Tuple[Callable[[list[str]], Awaitable[numpy.ndarray]], int]:
    """Generate LightRAG embedding function with proper error handling"""
    try:
        logger.info(f"Creating LightRAG embedding function for collection {collection.id}")
        embedding_svc, dim = await get_collection_embedding_service(collection)

        async def lightrag_embed_func(texts: list[str]) -> numpy.ndarray:
            try:
                embeddings = await embedding_svc.aembed_documents(texts)
                return numpy.array(embeddings)
            except Exception as e:
                logger.error(f"Embedding generation failed for {len(texts)} texts: {str(e)}")
                raise LightRAGServiceError(f"Embedding generation failed: {str(e)}") from e

        logger.info(f"Successfully created embedding function with dimension: {dim}")
        return lightrag_embed_func, dim

    except Exception as e:
        logger.error(f"Failed to generate LightRAG embedding function for collection {collection.id}: {str(e)}")
        raise LightRAGInitializationError(f"Failed to create embedding function: {str(e)}") from e


async def create_and_initialize_lightrag(
    collection_id: str,
    llm_func: Callable[..., Awaitable[str]],
    embed_impl: Callable[[List[str]], Awaitable[numpy.ndarray]],
    embed_dim: int,
) -> LightRagHolder:
    """
    Creates the LightRAG dependencies, instantiates the object for a specific collection,
    and runs its asynchronous initializers using supplied callable implementations.
    Returns a fully ready LightRagHolder for the given collection.

    Args:
        collection_id: The collection ID for this LightRAG instance.
        llm_func: Async callable that produces LLM completions.
        embed_impl: Async callable that produces embeddings.
        embed_dim: Embedding dimension.
    """
    logger.info(f"Creating and initializing LightRAG object for collection: '{collection_id}'")

    try:
        LIGHTRAG_KV_STORAGE = os.environ.get("LIGHTRAG_KV_STORAGE")
        LIGHTRAG_VECTOR_STORAGE = os.environ.get("LIGHTRAG_VECTOR_STORAGE")
        LIGHTRAG_GRAPH_STORAGE = os.environ.get("LIGHTRAG_GRAPH_STORAGE")
        LIGHTRAG_DOC_STATUS_STORAGE = os.environ.get("LIGHTRAG_DOC_STATUS_STORAGE")

        # default values for kg storage
        os.environ["EMBEDDING_BATCH_NUM"] = 32
        os.environ["COSINE_THRESHOLD"] = 0.2

        await checkAndConfigureNeo4jStorage(LIGHTRAG_GRAPH_STORAGE)

        await checkAndConfigurePostgresqlStorage(
            LIGHTRAG_DOC_STATUS_STORAGE, LIGHTRAG_GRAPH_STORAGE, LIGHTRAG_KV_STORAGE, LIGHTRAG_VECTOR_STORAGE
        )

        rag = LightRAG(
            workspace=collection_id,
            chunk_token_size=LightRAGConfig.CHUNK_TOKEN_SIZE,
            chunk_overlap_token_size=LightRAGConfig.CHUNK_OVERLAP_TOKEN_SIZE,
            llm_model_func=llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=embed_dim,
                max_token_size=LightRAGConfig.EMBEDDING_MAX_TOKEN_SIZE,
                func=embed_impl,
            ),
            cosine_better_than_threshold=0.2,
            max_parallel_insert=LightRAGConfig.MAX_PARALLEL_INSERT,
            llm_model_max_async=LightRAGConfig.LLM_MODEL_MAX_ASYNC,
            entity_extract_max_gleaning=LightRAGConfig.ENTITY_EXTRACT_MAX_GLEANING,
            addon_params={
                "language": LightRAGConfig.DEFAULT_LANGUAGE,
            },
            kv_storage=LIGHTRAG_KV_STORAGE,
            vector_storage=LIGHTRAG_VECTOR_STORAGE,
            graph_storage=LIGHTRAG_GRAPH_STORAGE,
            doc_status_storage=LIGHTRAG_DOC_STATUS_STORAGE,
        )

        await rag.initialize_storages()

        logger.info(f"LightRAG object for collection '{collection_id}' successfully initialized")
        return LightRagHolder(rag=rag, llm_func=llm_func, embed_impl=embed_impl, collection_id=collection_id)

    except Exception as e:
        logger.error(f"Failed to create and initialize LightRAG for collection '{collection_id}': {str(e)}")
        raise LightRAGInitializationError(f"LightRAG initialization failed: {str(e)}") from e


async def checkAndConfigurePostgresqlStorage(
    LIGHTRAG_DOC_STATUS_STORAGE, LIGHTRAG_GRAPH_STORAGE, LIGHTRAG_KV_STORAGE, LIGHTRAG_VECTOR_STORAGE
):
    # Check and configure PostgreSQL storage if used
    using_pg_storage = any(
        [
            LIGHTRAG_KV_STORAGE == "PGKVStorage",
            LIGHTRAG_VECTOR_STORAGE == "PGVectorStorage",
            LIGHTRAG_GRAPH_STORAGE == "PGGraphStorage",
            LIGHTRAG_DOC_STATUS_STORAGE == "PGDocStatusStorage",
            # Add sync versions
            LIGHTRAG_KV_STORAGE == "PGSyncKVStorage",
            LIGHTRAG_VECTOR_STORAGE == "PGSyncVectorStorage",
            LIGHTRAG_DOC_STATUS_STORAGE == "PGSyncDocStatusStorage",
            # Ops Sync
            LIGHTRAG_KV_STORAGE == "PGOpsSyncKVStorage",
            LIGHTRAG_VECTOR_STORAGE == "PGOpsSyncVectorStorage",
            LIGHTRAG_DOC_STATUS_STORAGE == "PGOpsDocStatusStorage",
        ]
    )
    if using_pg_storage:
        logger.info("LightRAG is configured to use PostgreSQL storage, checking environment variables...")

        POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
        POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
        POSTGRES_USER = os.environ.get("POSTGRES_USER")
        POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
        POSTGRES_DATABASE = os.environ.get("POSTGRES_DB")

        # Validate required PostgreSQL environment variables
        missing_pg_vars = []
        if not POSTGRES_HOST:
            missing_pg_vars.append("POSTGRES_HOST")
        if not POSTGRES_USER:
            missing_pg_vars.append("POSTGRES_USER")
        if not POSTGRES_PASSWORD:
            missing_pg_vars.append("POSTGRES_PASSWORD")
        if not POSTGRES_DATABASE:
            missing_pg_vars.append("POSTGRES_DB")

        if missing_pg_vars:
            raise LightRAGInitializationError(
                f"PostgreSQL storage requires the following environment variables: {', '.join(missing_pg_vars)}"
            )

        # Set PostgreSQL environment variables for LightRAG
        os.environ["POSTGRES_HOST"] = POSTGRES_HOST
        os.environ["POSTGRES_PORT"] = POSTGRES_PORT
        os.environ["POSTGRES_USER"] = POSTGRES_USER
        os.environ["POSTGRES_PASSWORD"] = POSTGRES_PASSWORD
        os.environ["POSTGRES_DATABASE"] = POSTGRES_DATABASE

        # Log which storage types are using PostgreSQL
        pg_storage_in_use = []
        if LIGHTRAG_KV_STORAGE in ["PGKVStorage", "PGSyncKVStorage"]:
            pg_storage_in_use.append(f"KV({LIGHTRAG_KV_STORAGE})")
        if LIGHTRAG_VECTOR_STORAGE in ["PGVectorStorage", "PGSyncVectorStorage"]:
            pg_storage_in_use.append(f"Vector({LIGHTRAG_VECTOR_STORAGE})")
        if LIGHTRAG_GRAPH_STORAGE == "PGGraphStorage":
            pg_storage_in_use.append(f"Graph({LIGHTRAG_GRAPH_STORAGE})")
        if LIGHTRAG_DOC_STATUS_STORAGE in ["PGDocStatusStorage", "PGSyncDocStatusStorage"]:
            pg_storage_in_use.append(f"DocStatus({LIGHTRAG_DOC_STATUS_STORAGE})")

        logger.info(
            f"PostgreSQL configuration: Host={POSTGRES_HOST}:{POSTGRES_PORT}, "
            f"Database={POSTGRES_DATABASE}, User={POSTGRES_USER}, "
        )


async def checkAndConfigureNeo4jStorage(LIGHTRAG_GRAPH_STORAGE):
    # Check and configure Neo4J storage if used
    if LIGHTRAG_GRAPH_STORAGE in ["Neo4JStorage", "Neo4JSyncStorage"]:
        logger.info(f"LightRAG is configured to use {LIGHTRAG_GRAPH_STORAGE} as graph storage, checking environment variables...")

        NEO4J_HOST = os.environ.get("NEO4J_HOST")
        NEO4J_PORT = os.environ.get("NEO4J_PORT", "7687")
        NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
        NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

        # Validate required Neo4J environment variables
        missing_neo4j_vars = []
        if not NEO4J_HOST:
            missing_neo4j_vars.append("NEO4J_HOST")
        if not NEO4J_USERNAME:
            missing_neo4j_vars.append("NEO4J_USERNAME")
        if not NEO4J_PASSWORD:
            missing_neo4j_vars.append("NEO4J_PASSWORD")

        if missing_neo4j_vars:
            raise LightRAGInitializationError(
                f"{LIGHTRAG_GRAPH_STORAGE} requires the following environment variables: {', '.join(missing_neo4j_vars)}"
            )

        NEO4J_URI = f"neo4j://{NEO4J_HOST}:{NEO4J_PORT}"

        # Set Neo4J environment variables for LightRAG
        os.environ["NEO4J_URI"] = NEO4J_URI
        os.environ["NEO4J_USERNAME"] = NEO4J_USERNAME
        os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD

        logger.info(f"{LIGHTRAG_GRAPH_STORAGE} configuration: URI={NEO4J_URI}, Username={NEO4J_USERNAME}")


# Module-level cache management
class LightRAGCache:
    """Thread-safe cache for LightRAG instances"""

    def __init__(self):
        self._instances: Dict[str, LightRagHolder] = {}
        # Use the new concurrent control system
        self._lock = get_graph_cache_lock()

    async def get(self, collection_id: str) -> Optional[LightRagHolder]:
        """Get cached instance"""
        async with self._lock:
            return self._instances.get(collection_id)

    async def set(self, collection_id: str, holder: LightRagHolder) -> None:
        """Set cached instance"""
        async with self._lock:
            self._instances[collection_id] = holder
            logger.info(f"Cached LightRAG instance for collection '{collection_id}'")

    async def remove(self, collection_id: str) -> bool:
        """Remove cached instance"""
        async with self._lock:
            if collection_id in self._instances:
                del self._instances[collection_id]
                logger.info(f"Removed LightRAG instance from cache for collection '{collection_id}'")
                return True
            return False

    async def clear(self) -> None:
        """Clear all cached instances"""
        async with self._lock:
            count = len(self._instances)
            self._instances.clear()
            logger.info(f"Cleared {count} LightRAG instances from cache")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            return {
                "total_instances": len(self._instances),
                "collections": list(self._instances.keys()),
                "creation_times": {col: holder.creation_time.isoformat() for col, holder in self._instances.items()},
            }


# Global cache instance
_cache = LightRAGCache()


async def get_lightrag_holder(collection: Collection, use_cache: bool = True) -> LightRagHolder:
    """
    Get or create a LightRAG holder for the given collection.
    Uses caching to avoid repeated initialization when use_cache=True.

    Args:
        collection: The collection to create LightRAG holder for
        use_cache: Whether to use cache. If False, always creates a new instance.
    """
    collection_id: str = str(collection.id)

    if not collection_id:
        raise ValueError("A valid collection_id must be provided.")

    # Try to get from cache first only if use_cache is True
    if use_cache:
        cached_holder = await _cache.get(collection_id)
        if cached_holder:
            logger.debug(f"Using cached LightRAG instance for collection '{collection_id}'")
            return cached_holder

    cache_status = "cache miss" if use_cache else "cache disabled"
    logger.info(f"Initializing new LightRAG instance for collection '{collection_id}' ({cache_status})")

    try:
        # Create new instance
        embed_func, dim = await gen_lightrag_embed_func(collection=collection)
        llm_func = await gen_lightrag_llm_func(collection=collection)

        if not llm_func:
            raise LightRAGInitializationError("Failed to create LLM function - no suitable MSP found")

        holder = await create_and_initialize_lightrag(collection_id, llm_func, embed_func, embed_dim=dim)

        # Cache the new instance only if use_cache is True
        if use_cache:
            await _cache.set(collection_id, holder)
            logger.info(f"LightRAG instance for collection '{collection_id}' initialized and cached successfully")
        else:
            logger.info(f"LightRAG instance for collection '{collection_id}' initialized (not cached)")

        return holder

    except Exception as e:
        # Clean up any partial cache entries if we were using cache
        if use_cache:
            await _cache.remove(collection_id)
        logger.error(f"Failed to initialize LightRAG instance for collection '{collection_id}': {str(e)}")
        raise LightRAGInitializationError(
            f"Failed during LightRAG instance creation/initialization for collection '{collection_id}'"
        ) from e


async def reload_lightrag_holder(collection: Collection) -> LightRagHolder:
    """
    Reload a LightRAG holder by removing the cached instance and creating a new one.
    """
    collection_id: str = str(collection.id)
    logger.info(f"Reloading LightRAG holder for collection '{collection_id}'")

    await _cache.remove(collection_id)
    return await get_lightrag_holder(collection)


async def delete_lightrag_holder(collection: Collection) -> bool:
    """
    Delete a LightRAG holder from cache.
    Returns True if an instance was removed, False if it wasn't cached.
    """
    collection_id: str = str(collection.id)
    if not collection_id:
        return False

    return await _cache.remove(collection_id)


async def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about the LightRAG cache"""
    return await _cache.get_stats()


async def clear_all_cache() -> None:
    """Clear all cached LightRAG instances"""
    await _cache.clear()


def get_graph_cache_lock():
    """Get the global lock for LightRAG cache operations"""
    return get_or_create_lock("lightrag_cache_operations")
