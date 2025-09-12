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

import asyncio
import logging
import os
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import numpy

from aperag.db.models import Collection
from aperag.db.ops import db_ops
from aperag.graph.lightrag import LightRAG
from aperag.graph.lightrag.utils import EmbeddingFunc
from aperag.llm.embed.base_embedding import get_collection_embedding_service_sync
from aperag.llm.llm_error_types import (
    EmbeddingError,
    ProviderNotFoundError,
)
from aperag.schema.utils import parseCollectionConfig

logger = logging.getLogger(__name__)


# Configuration constants
class LightRAGConfig:
    """Centralized configuration for LightRAG"""

    CHUNK_TOKEN_SIZE = 1200
    CHUNK_OVERLAP_TOKEN_SIZE = 100
    LLM_MODEL_MAX_ASYNC = 20
    COSINE_BETTER_THAN_THRESHOLD = 0.2
    MAX_BATCH_SIZE = 32
    ENTITY_EXTRACT_MAX_GLEANING = 0
    SUMMARY_TO_MAX_TOKENS = 2000
    FORCE_LLM_SUMMARY_ON_MERGE = 10
    EMBEDDING_MAX_TOKEN_SIZE = 8192
    # DEFAULT_LANGUAGE = "Simplified Chinese"
    DEFAULT_LANGUAGE = "The same language like input text"


class LightRAGError(Exception):
    """Base exception for LightRAG operations"""

    pass


async def create_lightrag_instance(collection: Collection) -> LightRAG:
    """
    Create a new LightRAG instance for the given collection.
    Since LightRAG is now stateless, we create a fresh instance each time.
    """
    collection_id = str(collection.id)

    try:
        # Generate embedding and LLM functions
        embed_func, embed_dim = await _gen_embed_func(collection)
        llm_func = await _gen_llm_func(collection)

        # Get storage configuration from environment
        # -- 由于Windows环境不便设置环境变量，此处采用默认值设置
        kv_storage = os.environ.get("GRAPH_INDEX_KV_STORAGE", default='PGOpsSyncKVStorage')
        vector_storage = os.environ.get("GRAPH_INDEX_VECTOR_STORAGE", default='PGOpsSyncVectorStorage')
        graph_storage = os.environ.get("GRAPH_INDEX_GRAPH_STORAGE", default='PGOpsSyncGraphStorage')

        # Configure storage backends
        await _configure_storage_backends(kv_storage, vector_storage, graph_storage)

        # Create LightRAG instance
        rag = LightRAG(
            workspace=collection_id,
            chunk_token_size=LightRAGConfig.CHUNK_TOKEN_SIZE,
            chunk_overlap_token_size=LightRAGConfig.CHUNK_OVERLAP_TOKEN_SIZE,
            llm_model_func=llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=embed_dim,
                max_token_size=LightRAGConfig.EMBEDDING_MAX_TOKEN_SIZE,
                func=embed_func,
            ),
            cosine_better_than_threshold=LightRAGConfig.COSINE_BETTER_THAN_THRESHOLD,
            max_batch_size=LightRAGConfig.MAX_BATCH_SIZE,
            llm_model_max_async=LightRAGConfig.LLM_MODEL_MAX_ASYNC,
            entity_extract_max_gleaning=LightRAGConfig.ENTITY_EXTRACT_MAX_GLEANING,
            summary_to_max_tokens=LightRAGConfig.SUMMARY_TO_MAX_TOKENS,
            force_llm_summary_on_merge=LightRAGConfig.FORCE_LLM_SUMMARY_ON_MERGE,
            addon_params={"language": LightRAGConfig.DEFAULT_LANGUAGE},
            kv_storage=kv_storage,
            vector_storage=vector_storage,
            graph_storage=graph_storage,
        )

        await rag.initialize_storages()
        return rag

    except Exception as e:
        logger.error(f"Failed to create LightRAG instance for collection '{collection_id}': {str(e)}")
        raise LightRAGError(f"Failed to create LightRAG instance: {str(e)}") from e


# --- Celery Support Functions ---


def process_document_for_celery(collection: Collection, content: str, doc_id: str, file_path: str) -> Dict[str, Any]:
    """
    Process a document in a synchronous context (for Celery).
    Creates a new event loop and LightRAG instance for each call.
    """
    return _run_in_new_loop(_process_document_async(collection, content, doc_id, file_path))


def delete_document_for_celery(collection: Collection, doc_id: str) -> Dict[str, Any]:
    """
    Delete a document in a synchronous context (for Celery).
    Creates a new event loop and LightRAG instance for each call.
    """
    return _run_in_new_loop(_delete_document_async(collection, doc_id))


async def _process_document_async(
    collection: Collection,
    content: str,
    doc_id: str,
    file_path: str,
) -> Dict[str, Any]:
    """Process document using LightRAG's stateless interfaces"""
    rag = await create_lightrag_instance(collection)

    try:
        logger.info(f"Processing document {doc_id}")

        if not content:
            # The parser couldn't extract any text content from the document;
            # it might be a purely image-based document.
            return {
                "status": "success",
                "doc_id": doc_id,
                "chunks_created": 0,
                "entities_extracted": 0,
                "relations_extracted": 0,
            }

        # Insert and chunk document
        chunk_result = await rag.ainsert_and_chunk_document(
            documents=[content], doc_ids=[doc_id], file_paths=[file_path]
        )

        results = chunk_result.get("results", [])
        if not results:
            return {
                "status": "warning",
                "doc_id": doc_id,
                "message": "No processing results returned",
                "chunks_created": 0,
                "entities_extracted": 0,
                "relations_extracted": 0,
            }

        # Process results
        total_stats = {"chunks_created": 0, "entities_extracted": 0, "relations_extracted": 0, "documents": []}

        for doc_result in results:
            doc_result_id = doc_result.get("doc_id")
            chunks_data = doc_result.get("chunks_data", {})
            chunk_count = doc_result.get("chunk_count", 0)

            if chunks_data:
                # Build graph index
                graph_result = await rag.aprocess_graph_indexing(chunks=chunks_data, collection_id=str(collection.id))

                total_stats["chunks_created"] += chunk_count
                total_stats["entities_extracted"] += graph_result.get("entities_extracted", 0)
                total_stats["relations_extracted"] += graph_result.get("relations_extracted", 0)

                total_stats["documents"].append(
                    {
                        "doc_id": doc_result_id,
                        "chunks_created": chunk_count,
                        "entities_extracted": graph_result.get("entities_extracted", 0),
                        "relations_extracted": graph_result.get("relations_extracted", 0),
                    }
                )

        return {"status": "success", "doc_id": doc_id, **total_stats}

    finally:
        await rag.finalize_storages()


async def _delete_document_async(collection: Collection, doc_id: str) -> Dict[str, Any]:
    """Delete a document from LightRAG"""
    rag = await create_lightrag_instance(collection)

    try:
        await rag.adelete_by_doc_id(str(doc_id))
        logger.info(f"Deleted document {doc_id} from LightRAG")
        return {"status": "success", "doc_id": doc_id, "message": "Document deleted successfully"}
    finally:
        await rag.finalize_storages()


def _run_in_new_loop(coro: Awaitable) -> Any:
    """Run an async function in a new event loop (for Celery compatibility)"""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.wait(pending, timeout=1.0))
        except Exception:
            pass
        finally:
            loop.close()
            asyncio.set_event_loop(None)


# --- Internal Helper Functions ---


async def _gen_embed_func(
    collection: Collection,
) -> Tuple[Callable[[list[str]], Awaitable[numpy.ndarray]], int]:
    """Generate embedding function for LightRAG"""
    try:
        embedding_svc, dim = get_collection_embedding_service_sync(collection)

        async def embed_func(texts: list[str]) -> numpy.ndarray:
            embeddings = await embedding_svc.aembed_documents(texts)
            return numpy.array(embeddings)

        return embed_func, dim
    except (ProviderNotFoundError, EmbeddingError) as e:
        # Configuration or embedding-specific errors
        logger.error(f"Failed to create embedding function - configuration error: {str(e)}")
        raise LightRAGError(f"Embedding configuration error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Failed to create embedding function: {str(e)}")
        raise LightRAGError(f"Failed to create embedding function: {str(e)}") from e


async def _gen_llm_func(collection: Collection) -> Callable[..., Awaitable[str]]:
    """Generate LLM function for LightRAG"""
    try:
        config = parseCollectionConfig(collection.config)
        llm_provider_name = config.completion.model_service_provider
        api_key = db_ops.query_provider_api_key(llm_provider_name, collection.user)
        if not api_key:
            raise Exception(f"API KEY not found for LLM Provider:{llm_provider_name}")

        # Get base_url from LLMProvider
        llm_provider = db_ops.query_llm_provider_by_name(llm_provider_name)
        base_url = llm_provider.base_url

        async def llm_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: List = [],
            max_tokens: Optional[int] = None,
            **kwargs,
        ) -> str:
            from aperag.llm.completion.completion_service import CompletionService

            completion_service = CompletionService(
                provider=config.completion.custom_llm_provider,
                model=config.completion.model,
                base_url=base_url,
                api_key=api_key,
                temperature=config.completion.temperature,
                max_tokens=max_tokens,
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if history_messages:
                messages.extend(history_messages)

            full_response = await completion_service.agenerate(
                history=messages, prompt=prompt, images=[], memory=bool(messages)
            )

            return full_response

        return llm_func

    except Exception as e:
        logger.error(f"Failed to create LLM function: {str(e)}")
        raise LightRAGError(f"Failed to create LLM function: {str(e)}") from e


async def _configure_storage_backends(kv_storage, vector_storage, graph_storage):
    """Configure storage backends based on environment variables"""

    # Configure PostgreSQL if needed
    using_pg = any(
        [
            kv_storage in ["PGKVStorage", "PGSyncKVStorage", "PGOpsSyncKVStorage"],
            vector_storage in ["PGVectorStorage", "PGSyncVectorStorage", "PGOpsSyncVectorStorage"],
            graph_storage == "PGGraphStorage",
        ]
    )

    if using_pg:
        _configure_postgresql()


def _configure_postgresql():
    """Configure PostgreSQL environment variables"""
    # -- 手动设置postgresql的环境变量
    os.environ["POSTGRES_HOST"] = "pg-cluster-postgresql-postgresql"
    os.environ["POSTGRES_USER"] = "postgres"
    os.environ["POSTGRES_PASSWORD"] = "postgres"
    os.environ["POSTGRES_DB"] = "postgres"
    required_vars = ["POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        raise LightRAGError(f"PostgreSQL storage requires: {', '.join(missing_vars)}")
