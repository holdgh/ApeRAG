import asyncio
import datetime
import json
import os
import logging
from dataclasses import dataclass, field
from datetime import timezone
from typing import Any, Union, final, List, Dict
import numpy as np
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from aperag.graph.lightrag.types import KnowledgeGraph, KnowledgeGraphEdge, KnowledgeGraphNode

from ..base import (
    BaseGraphStorage,
    BaseKVStorage,
    BaseVectorStorage,
    DocProcessingStatus,
    DocStatus,
    DocStatusStorage,
)
from ..namespace import NameSpace, is_namespace
from ..utils import logger

# Import sync connection manager
try:
    from aperag.db.postgres_sync_manager import PostgreSQLSyncConnectionManager
except ImportError:
    PostgreSQLSyncConnectionManager = None

from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env", override=False)

# Get maximum number of graph nodes from environment variable
MAX_GRAPH_NODES = int(os.getenv("MAX_GRAPH_NODES", 1000))


def namespace_to_table_name(namespace: str) -> str:
    """Map namespace to table name."""
    NAMESPACE_TABLE_MAP = {
        NameSpace.KV_STORE_FULL_DOCS: "LIGHTRAG_DOC_FULL",
        NameSpace.KV_STORE_TEXT_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
        NameSpace.VECTOR_STORE_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
        NameSpace.VECTOR_STORE_ENTITIES: "LIGHTRAG_VDB_ENTITY",
        NameSpace.VECTOR_STORE_RELATIONSHIPS: "LIGHTRAG_VDB_RELATION",
        NameSpace.DOC_STATUS: "LIGHTRAG_DOC_STATUS",
        NameSpace.KV_STORE_LLM_RESPONSE_CACHE: "LIGHTRAG_LLM_CACHE",
    }
    
    for k, v in NAMESPACE_TABLE_MAP.items():
        if is_namespace(namespace, k):
            return v
    return None


@final
@dataclass
class PGSyncKVStorage(BaseKVStorage):
    """
    PostgreSQL KV storage implementation using sync driver with async interface.
    This avoids event loop issues while maintaining compatibility with async code.
    """
    
    def __post_init__(self):
        self._max_batch_size = self.global_config["embedding_batch_num"]

    async def initialize(self):
        """Initialize storage."""
        if PostgreSQLSyncConnectionManager is None:
            raise RuntimeError("PostgreSQL sync connection manager is not available")
        
        # Initialize connection manager
        await asyncio.to_thread(PostgreSQLSyncConnectionManager.initialize)
        logger.info(f"PGSyncKVStorage initialized for workspace '{PostgreSQLSyncConnectionManager.get_workspace()}'")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGSyncKVStorage finalized for workspace '{PostgreSQLSyncConnectionManager.get_workspace()}'")

    async def get_all(self) -> dict[str, Any]:
        """Get all data from storage."""
        def _sync_get_all():
            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                logger.error(f"Unknown namespace for get_all: {self.namespace}")
                return {}

            sql = f"SELECT * FROM {table_name} WHERE workspace=%s"
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (workspace,), fetch_all=True
            )
            
            if is_namespace(self.namespace, NameSpace.KV_STORE_LLM_RESPONSE_CACHE):
                result_dict = {}
                for row in results:
                    mode = row["mode"]
                    if mode not in result_dict:
                        result_dict[mode] = {}
                    result_dict[mode][row["id"]] = dict(row)
                return result_dict
            else:
                return {row["id"]: dict(row) for row in results}
        
        return await asyncio.to_thread(_sync_get_all)

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get data by id."""
        def _sync_get_by_id():
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            
            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                sql = "SELECT id, COALESCE(content, '') as content FROM LIGHTRAG_DOC_FULL WHERE workspace=%s AND id=%s"
            elif is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                sql = """SELECT id, tokens, COALESCE(content, '') as content,
                        chunk_order_index, full_doc_id, file_path
                        FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=%s AND id=%s"""
            elif is_namespace(self.namespace, NameSpace.KV_STORE_LLM_RESPONSE_CACHE):
                sql = """SELECT id, original_prompt, COALESCE(return_value, '') as "return", mode
                        FROM LIGHTRAG_LLM_CACHE WHERE workspace=%s AND id=%s"""
            else:
                table_name = namespace_to_table_name(self.namespace)
                sql = f"SELECT * FROM {table_name} WHERE workspace=%s AND id=%s"
            
            result = PostgreSQLSyncConnectionManager.execute_query(
                sql, (workspace, id), fetch_one=True
            )
            
            return dict(result) if result else None
        
        return await asyncio.to_thread(_sync_get_by_id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get data by multiple ids."""
        def _sync_get_by_ids():
            if not ids:
                return []
                
            table_name = namespace_to_table_name(self.namespace)
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            ids_placeholder = ','.join(['%s'] * len(ids))
            
            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                sql = f"SELECT id, COALESCE(content, '') as content FROM LIGHTRAG_DOC_FULL WHERE workspace=%s AND id IN ({ids_placeholder})"
            elif is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                sql = f"""SELECT id, tokens, COALESCE(content, '') as content,
                         chunk_order_index, full_doc_id, file_path
                         FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=%s AND id IN ({ids_placeholder})"""
            else:
                sql = f"SELECT * FROM {table_name} WHERE workspace=%s AND id IN ({ids_placeholder})"
            
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (workspace, *ids), fetch_all=True
            )
            
            return [dict(row) for row in results]
        
        return await asyncio.to_thread(_sync_get_by_ids)

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out existing keys."""
        def _sync_filter_keys():
            if not keys:
                return set()
                
            table_name = namespace_to_table_name(self.namespace)
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            keys_list = list(keys)
            ids_placeholder = ','.join(['%s'] * len(keys_list))
            
            sql = f"SELECT id FROM {table_name} WHERE workspace=%s AND id IN ({ids_placeholder})"
            
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (workspace, *keys_list), fetch_all=True
            )
            
            existing_keys = {row["id"] for row in results}
            return keys - existing_keys
        
        return await asyncio.to_thread(_sync_filter_keys)

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Insert or update data."""
        def _sync_upsert():
            if not data:
                return
                
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            
            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                sql = """INSERT INTO LIGHTRAG_DOC_FULL (id, content, workspace)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (workspace,id) DO UPDATE
                        SET content = EXCLUDED.content, update_time = CURRENT_TIMESTAMP"""
                
                for k, v in data.items():
                    PostgreSQLSyncConnectionManager.execute_query(
                        sql, (k, v["content"], workspace)
                    )
                    
            elif is_namespace(self.namespace, NameSpace.KV_STORE_LLM_RESPONSE_CACHE):
                sql = """INSERT INTO LIGHTRAG_LLM_CACHE(workspace,id,original_prompt,return_value,mode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (workspace,mode,id) DO UPDATE
                        SET original_prompt = EXCLUDED.original_prompt,
                        return_value=EXCLUDED.return_value,
                        mode=EXCLUDED.mode,
                        update_time = CURRENT_TIMESTAMP"""
                
                for mode, items in data.items():
                    for k, v in items.items():
                        PostgreSQLSyncConnectionManager.execute_query(
                            sql, (workspace, k, v["original_prompt"], v["return"], mode)
                        )
        
        await asyncio.to_thread(_sync_upsert)

    async def delete(self, ids: list[str]) -> None:
        """Delete records by IDs."""
        def _sync_delete():
            if not ids:
                return
                
            table_name = namespace_to_table_name(self.namespace)
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            ids_placeholder = ','.join(['%s'] * len(ids))
            
            sql = f"DELETE FROM {table_name} WHERE workspace=%s AND id IN ({ids_placeholder})"
            PostgreSQLSyncConnectionManager.execute_query(sql, (workspace, *ids))
        
        await asyncio.to_thread(_sync_delete)

    async def drop(self) -> dict[str, str]:
        """Drop the storage."""
        def _sync_drop():
            try:
                table_name = namespace_to_table_name(self.namespace)
                if not table_name:
                    return {"status": "error", "message": f"Unknown namespace: {self.namespace}"}
                
                workspace = PostgreSQLSyncConnectionManager.get_workspace()
                sql = f"DELETE FROM {table_name} WHERE workspace=%s"
                PostgreSQLSyncConnectionManager.execute_query(sql, (workspace,))
                
                return {"status": "success", "message": "data dropped"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        return await asyncio.to_thread(_sync_drop)

    async def get_by_mode_and_id(self, mode: str, id: str) -> Union[dict, None]:
        """Specifically for llm_response_cache."""
        def _sync_get_by_mode_and_id():
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            
            if is_namespace(self.namespace, NameSpace.KV_STORE_LLM_RESPONSE_CACHE):
                sql = """SELECT id, original_prompt, COALESCE(return_value, '') as "return", mode
                        FROM LIGHTRAG_LLM_CACHE WHERE workspace=%s AND mode=%s AND id=%s"""
                
                results = PostgreSQLSyncConnectionManager.execute_query(
                    sql, (workspace, mode, id), fetch_all=True
                )
                
                res = {}
                for row in results:
                    res[row["id"]] = dict(row)
                return res
            else:
                return None
        
        return await asyncio.to_thread(_sync_get_by_mode_and_id)

    async def get_by_status(self, status: str) -> Union[list[dict[str, Any]], None]:
        """Specifically for llm_response_cache."""
        def _sync_get_by_status():
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            sql = """SELECT * FROM LIGHTRAG_LLM_CACHE WHERE workspace=%s AND status=%s"""
            
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (workspace, status), fetch_all=True
            )
            
            return [dict(row) for row in results] if results else []
        
        return await asyncio.to_thread(_sync_get_by_status)

    async def drop_cache_by_modes(self, modes: list[str] | None = None) -> bool:
        """Delete specific records from storage by cache mode."""
        def _sync_drop_cache_by_modes():
            if not modes:
                return False

            try:
                table_name = namespace_to_table_name(self.namespace)
                if not table_name or table_name != "LIGHTRAG_LLM_CACHE":
                    return False

                workspace = PostgreSQLSyncConnectionManager.get_workspace()
                modes_placeholder = ','.join(['%s'] * len(modes))
                sql = f"DELETE FROM {table_name} WHERE workspace=%s AND mode IN ({modes_placeholder})"
                
                PostgreSQLSyncConnectionManager.execute_query(sql, (workspace, *modes))
                logger.info(f"Deleted cache by modes: {modes}")
                return True
            except Exception as e:
                logger.error(f"Error deleting cache by modes {modes}: {e}")
                return False
        
        return await asyncio.to_thread(_sync_drop_cache_by_modes)


@final
@dataclass
class PGSyncVectorStorage(BaseVectorStorage):
    """
    PostgreSQL Vector storage implementation using sync driver with async interface.
    """
    
    def __post_init__(self):
        self._max_batch_size = self.global_config["embedding_batch_num"]
        config = self.global_config.get("vector_db_storage_cls_kwargs", {})
        cosine_threshold = config.get("cosine_better_than_threshold")
        if cosine_threshold is None:
            raise ValueError("cosine_better_than_threshold must be specified")
        self.cosine_better_than_threshold = cosine_threshold

    async def initialize(self):
        """Initialize storage."""
        if PostgreSQLSyncConnectionManager is None:
            raise RuntimeError("PostgreSQL sync connection manager is not available")
        
        await asyncio.to_thread(PostgreSQLSyncConnectionManager.initialize)
        logger.info(f"PGSyncVectorStorage initialized for workspace '{PostgreSQLSyncConnectionManager.get_workspace()}'")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGSyncVectorStorage finalized")

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Insert or update vector data."""
        # Handle embedding generation in async context first
        if data:
            list_data = [{"__id__": k, **v} for k, v in data.items()]
            contents = [v["content"] for v in data.values()]
            batches = [
                contents[i : i + self._max_batch_size]
                for i in range(0, len(contents), self._max_batch_size)
            ]
            
            embedding_tasks = [self.embedding_func(batch) for batch in batches]
            embeddings_list = await asyncio.gather(*embedding_tasks)
            embeddings = np.concatenate(embeddings_list)
            
            # Add embeddings to original data
            for i, (k, v) in enumerate(data.items()):
                v["__vector__"] = embeddings[i]
        
        def _sync_upsert():
            if not data:
                return
                
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            current_time = datetime.datetime.now(timezone.utc)
            
            # Process data
            list_data = [{"__id__": k, **v} for k, v in data.items()]
            
            # Insert data based on namespace
            for item in list_data:
                if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                    sql, data = self._upsert_chunks(item, current_time)
                    PostgreSQLSyncConnectionManager.execute_query(sql, data)
                    
                elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                    sql, data = self._upsert_entities(item, current_time)
                    PostgreSQLSyncConnectionManager.execute_query(sql, data)
                    
                elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                    sql, data = self._upsert_relationships(item, current_time)
                    PostgreSQLSyncConnectionManager.execute_query(sql, data)
        
        await asyncio.to_thread(_sync_upsert)

    async def query(self, query: str, top_k: int, ids: list[str] | None = None) -> list[dict[str, Any]]:
        """Query vectors."""
        # Generate query embedding
        embeddings = await self.embedding_func([query])
        embedding = embeddings[0]
        
        def _sync_query():
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            embedding_string = ",".join(map(str, embedding))
            
            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                sql = f"""
                WITH relevant_chunks AS (
                    SELECT id as chunk_id
                    FROM LIGHTRAG_DOC_CHUNKS
                    WHERE %s IS NULL OR full_doc_id = ANY(%s)
                )
                SELECT entity_name, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM
                    (
                        SELECT e.id, e.entity_name, e.create_time, 1 - (e.content_vector <=> '[{embedding_string}]'::vector) as distance
                        FROM LIGHTRAG_VDB_ENTITY e
                        JOIN relevant_chunks c ON c.chunk_id = ANY(e.chunk_ids)
                        WHERE e.workspace=%s
                    ) as chunk_distances
                    WHERE distance>%s
                    ORDER BY distance DESC
                    LIMIT %s
                """
                params = (ids, ids, workspace, self.cosine_better_than_threshold, top_k)
                
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                sql = f"""
                WITH relevant_chunks AS (
                    SELECT id as chunk_id
                    FROM LIGHTRAG_DOC_CHUNKS
                    WHERE %s IS NULL OR full_doc_id = ANY(%s)
                )
                SELECT source_id as src_id, target_id as tgt_id, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at
                FROM (
                    SELECT r.id, r.source_id, r.target_id, r.create_time, 1 - (r.content_vector <=> '[{embedding_string}]'::vector) as distance
                    FROM LIGHTRAG_VDB_RELATION r
                    JOIN relevant_chunks c ON c.chunk_id = ANY(r.chunk_ids)
                    WHERE r.workspace=%s
                ) filtered
                WHERE distance>%s
                ORDER BY distance DESC
                LIMIT %s
                """
                params = (ids, ids, workspace, self.cosine_better_than_threshold, top_k)
                
            else:  # VECTOR_STORE_CHUNKS
                sql = f"""
                WITH relevant_chunks AS (
                    SELECT id as chunk_id
                    FROM LIGHTRAG_DOC_CHUNKS
                    WHERE %s IS NULL OR full_doc_id = ANY(%s)
                )
                SELECT id, content, file_path, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM
                    (
                        SELECT id, content, file_path, create_time, 1 - (content_vector <=> '[{embedding_string}]'::vector) as distance
                        FROM LIGHTRAG_DOC_CHUNKS
                        WHERE workspace=%s
                        AND id IN (SELECT chunk_id FROM relevant_chunks)
                    ) as chunk_distances
                    WHERE distance>%s
                    ORDER BY distance DESC
                    LIMIT %s
                """
                params = (ids, ids, workspace, self.cosine_better_than_threshold, top_k)
            
            results = PostgreSQLSyncConnectionManager.execute_query(sql, params, fetch_all=True)
            return [dict(row) for row in results]
        
        return await asyncio.to_thread(_sync_query)

    async def delete(self, ids: list[str]) -> None:
        """Delete vectors by IDs."""
        def _sync_delete():
            if not ids:
                return
                
            table_name = namespace_to_table_name(self.namespace)
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            ids_placeholder = ','.join(['%s'] * len(ids))
            
            sql = f"DELETE FROM {table_name} WHERE workspace=%s AND id IN ({ids_placeholder})"
            PostgreSQLSyncConnectionManager.execute_query(sql, (workspace, *ids))
        
        await asyncio.to_thread(_sync_delete)

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get vector data by ID."""
        def _sync_get_by_id():
            table_name = namespace_to_table_name(self.namespace)
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            
            sql = f"SELECT *, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM {table_name} WHERE workspace=%s AND id=%s"
            result = PostgreSQLSyncConnectionManager.execute_query(sql, (workspace, id), fetch_one=True)
            
            return dict(result) if result else None
        
        return await asyncio.to_thread(_sync_get_by_id)

    async def drop(self) -> dict[str, str]:
        """Drop the storage."""
        def _sync_drop():
            try:
                table_name = namespace_to_table_name(self.namespace)
                if not table_name:
                    return {"status": "error", "message": f"Unknown namespace: {self.namespace}"}
                
                workspace = PostgreSQLSyncConnectionManager.get_workspace()
                sql = f"DELETE FROM {table_name} WHERE workspace=%s"
                PostgreSQLSyncConnectionManager.execute_query(sql, (workspace,))
                
                return {"status": "success", "message": "data dropped"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        return await asyncio.to_thread(_sync_drop)

    def _upsert_chunks(self, item: dict[str, Any], current_time: datetime.datetime) -> tuple[str, tuple]:
        """Prepare chunk upsert SQL and data."""
        try:
            sql = """INSERT INTO LIGHTRAG_DOC_CHUNKS (workspace, id, tokens,
                    chunk_order_index, full_doc_id, content, content_vector, file_path,
                    create_time, update_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (workspace,id) DO UPDATE
                    SET tokens=EXCLUDED.tokens,
                    chunk_order_index=EXCLUDED.chunk_order_index,
                    full_doc_id=EXCLUDED.full_doc_id,
                    content = EXCLUDED.content,
                    content_vector=EXCLUDED.content_vector,
                    file_path=EXCLUDED.file_path,
                    update_time = EXCLUDED.update_time"""
            
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            data = (
                workspace, item["__id__"], item["tokens"],
                item["chunk_order_index"], item["full_doc_id"],
                item["content"], json.dumps(item["__vector__"].tolist()),
                item["file_path"], current_time, current_time
            )
        except Exception as e:
            logger.error(f"Error to prepare upsert chunks: {e}, item: {item}")
            raise

        return sql, data

    def _upsert_entities(self, item: dict[str, Any], current_time: datetime.datetime) -> tuple[str, tuple]:
        """Prepare entity upsert SQL and data."""
        sql = """INSERT INTO LIGHTRAG_VDB_ENTITY (workspace, id, entity_name, content,
                content_vector, chunk_ids, file_path, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (workspace,id) DO UPDATE
                SET entity_name=EXCLUDED.entity_name,
                content=EXCLUDED.content,
                content_vector=EXCLUDED.content_vector,
                chunk_ids=EXCLUDED.chunk_ids,
                file_path=EXCLUDED.file_path,
                update_time=EXCLUDED.update_time"""
        
        source_id = item["source_id"]
        chunk_ids = source_id.split("<SEP>") if isinstance(source_id, str) and "<SEP>" in source_id else [source_id]
        
        workspace = PostgreSQLSyncConnectionManager.get_workspace()
        data = (
            workspace, item["__id__"], item["entity_name"],
            item["content"], json.dumps(item["__vector__"].tolist()),
            chunk_ids, item.get("file_path"), current_time, current_time
        )
        return sql, data

    def _upsert_relationships(self, item: dict[str, Any], current_time: datetime.datetime) -> tuple[str, tuple]:
        """Prepare relationship upsert SQL and data."""
        sql = """INSERT INTO LIGHTRAG_VDB_RELATION (workspace, id, source_id,
                target_id, content, content_vector, chunk_ids, file_path, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (workspace,id) DO UPDATE
                SET source_id=EXCLUDED.source_id,
                target_id=EXCLUDED.target_id,
                content=EXCLUDED.content,
                content_vector=EXCLUDED.content_vector,
                chunk_ids=EXCLUDED.chunk_ids,
                file_path=EXCLUDED.file_path,
                update_time = EXCLUDED.update_time"""
        
        source_id = item["source_id"]
        chunk_ids = source_id.split("<SEP>") if isinstance(source_id, str) and "<SEP>" in source_id else [source_id]
        
        workspace = PostgreSQLSyncConnectionManager.get_workspace()
        data = (
            workspace, item["__id__"], item["src_id"], item["tgt_id"],
            item["content"], json.dumps(item["__vector__"].tolist()),
            chunk_ids, item.get("file_path"), current_time, current_time
        )
        return sql, data

    async def delete_entity(self, entity_name: str) -> None:
        """Delete an entity by its name from the vector storage."""
        def _sync_delete_entity():
            try:
                workspace = PostgreSQLSyncConnectionManager.get_workspace()
                sql = "DELETE FROM LIGHTRAG_VDB_ENTITY WHERE workspace=%s AND entity_name=%s"
                
                PostgreSQLSyncConnectionManager.execute_query(sql, (workspace, entity_name))
                logger.debug(f"Successfully deleted entity {entity_name}")
            except Exception as e:
                logger.error(f"Error deleting entity {entity_name}: {e}")
        
        await asyncio.to_thread(_sync_delete_entity)

    async def delete_entity_relation(self, entity_name: str) -> None:
        """Delete all relations associated with an entity."""
        def _sync_delete_entity_relation():
            try:
                workspace = PostgreSQLSyncConnectionManager.get_workspace()
                sql = "DELETE FROM LIGHTRAG_VDB_RELATION WHERE workspace=%s AND (source_id=%s OR target_id=%s)"
                
                PostgreSQLSyncConnectionManager.execute_query(sql, (workspace, entity_name, entity_name))
                logger.debug(f"Successfully deleted relations for entity {entity_name}")
            except Exception as e:
                logger.error(f"Error deleting relations for entity {entity_name}: {e}")
        
        await asyncio.to_thread(_sync_delete_entity_relation)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get multiple vector data by their IDs."""
        def _sync_get_by_ids():
            if not ids:
                return []

            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                logger.error(f"Unknown namespace for IDs lookup: {self.namespace}")
                return []

            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            ids_placeholder = ','.join(['%s'] * len(ids))
            sql = f"SELECT *, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM {table_name} WHERE workspace=%s AND id IN ({ids_placeholder})"

            try:
                results = PostgreSQLSyncConnectionManager.execute_query(
                    sql, (workspace, *ids), fetch_all=True
                )
                return [dict(record) for record in results]
            except Exception as e:
                logger.error(f"Error retrieving vector data for IDs {ids}: {e}")
                return []
        
        return await asyncio.to_thread(_sync_get_by_ids)


@final
@dataclass
class PGSyncDocStatusStorage(DocStatusStorage):
    """
    PostgreSQL Doc Status storage implementation using sync driver.
    """

    async def initialize(self):
        """Initialize storage."""
        if PostgreSQLSyncConnectionManager is None:
            raise RuntimeError("PostgreSQL sync connection manager is not available")
        
        await asyncio.to_thread(PostgreSQLSyncConnectionManager.initialize)
        logger.info(f"PGSyncDocStatusStorage initialized")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGSyncDocStatusStorage finalized")

    async def get_by_id(self, id: str) -> Union[dict[str, Any], None]:
        """Get document status by ID."""
        def _sync_get_by_id():
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            sql = "SELECT * FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s AND id=%s"
            result = PostgreSQLSyncConnectionManager.execute_query(sql, (workspace, id), fetch_one=True)
            
            if result:
                return {
                    "content": result["content"],
                    "content_length": result["content_length"],
                    "content_summary": result["content_summary"],
                    "status": result["status"],
                    "chunks_count": result["chunks_count"],
                    "created_at": result["created_at"],
                    "updated_at": result["updated_at"],
                    "file_path": result["file_path"],
                }
            return None
        
        return await asyncio.to_thread(_sync_get_by_id)

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Update or insert document status."""
        def _sync_upsert():
            if not data:
                return
                
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            sql = """INSERT INTO LIGHTRAG_DOC_STATUS(workspace,id,content,content_summary,content_length,chunks_count,status,file_path,created_at,updated_at)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                     ON CONFLICT(id,workspace) DO UPDATE SET
                     content = EXCLUDED.content,
                     content_summary = EXCLUDED.content_summary,
                     content_length = EXCLUDED.content_length,
                     chunks_count = EXCLUDED.chunks_count,
                     status = EXCLUDED.status,
                     file_path = EXCLUDED.file_path,
                     created_at = EXCLUDED.created_at,
                     updated_at = EXCLUDED.updated_at"""
            
            for k, v in data.items():
                def parse_datetime(dt_str):
                    if dt_str is None:
                        return None
                    if isinstance(dt_str, (datetime.date, datetime.datetime)):
                        if isinstance(dt_str, datetime.datetime):
                            return dt_str.replace(tzinfo=None)
                        return dt_str
                    try:
                        dt = datetime.datetime.fromisoformat(dt_str)
                        return dt.replace(tzinfo=None)
                    except (ValueError, TypeError):
                        logger.warning(f"Unable to parse datetime string: {dt_str}")
                        return None
                
                created_at = parse_datetime(v.get("created_at"))
                updated_at = parse_datetime(v.get("updated_at"))
                
                PostgreSQLSyncConnectionManager.execute_query(sql, (
                    workspace, k, v["content"], v["content_summary"],
                    v["content_length"], v.get("chunks_count", -1),
                    v["status"], v["file_path"], created_at, updated_at
                ))
        
        await asyncio.to_thread(_sync_upsert)

    async def delete(self, ids: list[str]) -> None:
        """Delete records by IDs."""
        def _sync_delete():
            if not ids:
                return
                
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            ids_placeholder = ','.join(['%s'] * len(ids))
            sql = f"DELETE FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s AND id IN ({ids_placeholder})"
            PostgreSQLSyncConnectionManager.execute_query(sql, (workspace, *ids))
        
        await asyncio.to_thread(_sync_delete)

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter existing keys."""
        def _sync_filter_keys():
            if not keys:
                return set()
                
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            keys_list = list(keys)
            ids_placeholder = ','.join(['%s'] * len(keys_list))
            
            sql = f"SELECT id FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s AND id IN ({ids_placeholder})"
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (workspace, *keys_list), fetch_all=True
            )
            
            existing_keys = {row["id"] for row in results}
            return keys - existing_keys
        
        return await asyncio.to_thread(_sync_filter_keys)

    async def drop(self) -> dict[str, str]:
        """Drop the storage."""
        def _sync_drop():
            try:
                workspace = PostgreSQLSyncConnectionManager.get_workspace()
                sql = "DELETE FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s"
                PostgreSQLSyncConnectionManager.execute_query(sql, (workspace,))
                return {"status": "success", "message": "data dropped"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        return await asyncio.to_thread(_sync_drop)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get doc_chunks data by multiple IDs."""
        def _sync_get_by_ids():
            if not ids:
                return []

            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            ids_placeholder = ','.join(['%s'] * len(ids))
            sql = f"SELECT * FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s AND id IN ({ids_placeholder})"

            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (workspace, *ids), fetch_all=True
            )

            if not results:
                return []
            return [
                {
                    "content": row["content"],
                    "content_length": row["content_length"],
                    "content_summary": row["content_summary"],
                    "status": row["status"],
                    "chunks_count": row["chunks_count"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "file_path": row["file_path"],
                }
                for row in results
            ]
        
        return await asyncio.to_thread(_sync_get_by_ids)

    async def get_status_counts(self) -> dict[str, int]:
        """Get counts of documents in each status."""
        def _sync_get_status_counts():
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            sql = """SELECT status as "status", COUNT(1) as "count"
                       FROM LIGHTRAG_DOC_STATUS
                      where workspace=%s GROUP BY STATUS"""
            
            result = PostgreSQLSyncConnectionManager.execute_query(sql, (workspace,), fetch_all=True)
            counts = {}
            for doc in result:
                counts[doc["status"]] = doc["count"]
            return counts
        
        return await asyncio.to_thread(_sync_get_status_counts)

    async def get_docs_by_status(self, status) -> dict[str, dict]:
        """Get all documents with a specific status."""
        def _sync_get_docs_by_status():
            workspace = PostgreSQLSyncConnectionManager.get_workspace()
            sql = "select * from LIGHTRAG_DOC_STATUS where workspace=%s and status=%s"
            
            result = PostgreSQLSyncConnectionManager.execute_query(
                sql, (workspace, status.value), fetch_all=True
            )
            
            docs_by_status = {}
            for element in result:
                # Create a dictionary matching the expected DocProcessingStatus structure
                docs_by_status[element["id"]] = {
                    "content": element["content"],
                    "content_summary": element["content_summary"],
                    "content_length": element["content_length"],
                    "status": element["status"],
                    "created_at": element["created_at"],
                    "updated_at": element["updated_at"],
                    "chunks_count": element["chunks_count"],
                    "file_path": element["file_path"],
                }
            return docs_by_status
        
        return await asyncio.to_thread(_sync_get_docs_by_status)


class PGGraphQueryException(Exception):
    """Exception for the AGE queries."""

    def __init__(self, exception: Union[str, dict[str, Any]]) -> None:
        if isinstance(exception, dict):
            self.message = exception["message"] if "message" in exception else "unknown"
            self.details = exception["details"] if "details" in exception else "unknown"
        else:
            self.message = exception
            self.details = "unknown"

    def get_message(self) -> str:
        return self.message

    def get_details(self) -> Any:
        return self.details


@final
@dataclass
class PGSyncGraphStorage(BaseGraphStorage):
    """
    PostgreSQL Graph storage implementation using sync driver with Apache AGE.
    """
    
    def __post_init__(self):
        # Use the base namespace (storage_type) for graph name
        self.graph_name = self.storage_type or os.environ.get("AGE_GRAPH_NAME", "lightrag")

    async def initialize(self):
        """Initialize storage."""
        if PostgreSQLSyncConnectionManager is None:
            raise RuntimeError("PostgreSQL sync connection manager is not available")
        
        await asyncio.to_thread(PostgreSQLSyncConnectionManager.initialize)
        
        # Initialize Apache AGE graph
        def _sync_initialize_age():
            queries = [
                f"SELECT create_graph('{self.graph_name}')",
                f"SELECT create_vlabel('{self.graph_name}', 'base');",
                f"SELECT create_elabel('{self.graph_name}', 'DIRECTED');",
                f'CREATE INDEX CONCURRENTLY vertex_idx_node_id ON {self.graph_name}."_ag_label_vertex" (ag_catalog.agtype_access_operator(properties, \'"entity_id"\'::agtype))',
                f'CREATE INDEX CONCURRENTLY edge_sid_idx ON {self.graph_name}."_ag_label_edge" (start_id)',
                f'CREATE INDEX CONCURRENTLY edge_eid_idx ON {self.graph_name}."_ag_label_edge" (end_id)',
                f'CREATE INDEX CONCURRENTLY edge_seid_idx ON {self.graph_name}."_ag_label_edge" (start_id,end_id)',
                f'CREATE INDEX CONCURRENTLY directed_p_idx ON {self.graph_name}."DIRECTED" (id)',
                f'CREATE INDEX CONCURRENTLY directed_eid_idx ON {self.graph_name}."DIRECTED" (end_id)',
                f'CREATE INDEX CONCURRENTLY directed_sid_idx ON {self.graph_name}."DIRECTED" (start_id)',
                f'CREATE INDEX CONCURRENTLY directed_seid_idx ON {self.graph_name}."DIRECTED" (start_id,end_id)',
                f'CREATE INDEX CONCURRENTLY entity_p_idx ON {self.graph_name}."base" (id)',
                f'CREATE INDEX CONCURRENTLY entity_idx_node_id ON {self.graph_name}."base" (ag_catalog.agtype_access_operator(properties, \'"entity_id"\'::agtype))',
                f'CREATE INDEX CONCURRENTLY entity_node_id_gin_idx ON {self.graph_name}."base" using gin(properties)',
                f'ALTER TABLE {self.graph_name}."DIRECTED" CLUSTER ON directed_sid_idx',
            ]

            for query in queries:
                try:
                    PostgreSQLSyncConnectionManager.execute_query(query)
                except Exception:
                    continue  # Ignore errors for existing structures
        
        await asyncio.to_thread(_sync_initialize_age)
        logger.info(f"PGSyncGraphStorage initialized for graph '{self.graph_name}'")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGSyncGraphStorage finalized")

    @staticmethod
    def _normalize_node_id(node_id: str) -> str:
        """Normalize node ID to ensure special characters are properly handled in Cypher queries."""
        normalized_id = node_id
        normalized_id = normalized_id.replace("\\", "\\\\")
        normalized_id = normalized_id.replace('"', '\\"')
        return normalized_id

    @staticmethod
    def _record_to_dict(record: dict) -> dict[str, Any]:
        """Convert a record returned from an age query to a dictionary."""
        d = {}
        vertices = {}
        
        for k in record.keys():
            v = record[k]
            if isinstance(v, str) and "::" in v:
                if v.startswith("[") and v.endswith("]"):
                    if "::vertex" not in v:
                        continue
                    v = v.replace("::vertex", "")
                    vertexes = json.loads(v)
                    for vertex in vertexes:
                        vertices[vertex["id"]] = vertex.get("properties")
                else:
                    dtype = v.split("::")[-1]
                    v = v.split("::")[0]
                    if dtype == "vertex":
                        vertex = json.loads(v)
                        vertices[vertex["id"]] = vertex.get("properties")

        for k in record.keys():
            v = record[k]
            if isinstance(v, str) and "::" in v:
                if v.startswith("[") and v.endswith("]"):
                    if "::vertex" in v:
                        v = v.replace("::vertex", "")
                        d[k] = json.loads(v)
                    elif "::edge" in v:
                        v = v.replace("::edge", "")
                        d[k] = json.loads(v)
                    else:
                        continue
                else:
                    dtype = v.split("::")[-1]
                    v = v.split("::")[0]
                    if dtype == "vertex":
                        d[k] = json.loads(v)
                    elif dtype == "edge":
                        d[k] = json.loads(v)
            else:
                d[k] = v

        return d

    @staticmethod
    def _format_properties(properties: dict[str, Any], _id: Union[str, None] = None) -> str:
        """Convert a dictionary of properties to a string representation."""
        props = []
        for k, v in properties.items():
            prop = f"`{k}`: {json.dumps(v)}"
            props.append(prop)
        if _id is not None and "id" not in properties:
            props.append(
                f"id: {json.dumps(_id)}" if isinstance(_id, str) else f"id: {_id}"
            )
        return "{" + ", ".join(props) + "}"

    async def _query(self, query: str, readonly: bool = True, upsert: bool = False) -> list[dict[str, Any]]:
        """Query the graph by taking a cypher query."""
        def _sync_query():
            try:
                if readonly:
                    results = PostgreSQLSyncConnectionManager.execute_query(query, fetch_all=True)
                else:
                    PostgreSQLSyncConnectionManager.execute_query(query)
                    results = []
            except Exception as e:
                raise PGGraphQueryException({
                    "message": f"Error executing graph query: {query}",
                    "wrapped": query,
                    "detail": str(e),
                }) from e

            if results is None:
                result = []
            else:
                result = [self._record_to_dict(dict(d)) for d in results]

            return result
        
        return await asyncio.to_thread(_sync_query)

    async def has_node(self, node_id: str) -> bool:
        """Check if a node exists."""
        entity_name_label = self._normalize_node_id(node_id)
        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (n:base {{entity_id: "{entity_name_label}"}})
                     RETURN count(n) > 0 AS node_exists
                   $$) AS (node_exists bool)"""

        single_result = (await self._query(query))[0]
        return single_result["node_exists"]

    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        """Check if an edge exists between two nodes."""
        src_label = self._normalize_node_id(source_node_id)
        tgt_label = self._normalize_node_id(target_node_id)

        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (a:base {{entity_id: "{src_label}"}})-[r]-(b:base {{entity_id: "{tgt_label}"}})
                     RETURN COUNT(r) > 0 AS edge_exists
                   $$) AS (edge_exists bool)"""

        single_result = (await self._query(query))[0]
        return single_result["edge_exists"]

    async def get_node(self, node_id: str) -> dict[str, str] | None:
        """Get node by its label identifier."""
        label = self._normalize_node_id(node_id)
        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (n:base {{entity_id: "{label}"}})
                     RETURN n
                   $$) AS (n agtype)"""
        record = await self._query(query)
        if record:
            node = record[0]
            node_dict = node["n"]["properties"]

            if isinstance(node_dict, str):
                try:
                    node_dict = json.loads(node_dict)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse node string: {node_dict}")

            return node_dict
        return None

    async def node_degree(self, node_id: str) -> int:
        """Get the degree of a node."""
        label = self._normalize_node_id(node_id)
        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (n:base {{entity_id: "{label}"}})-[r]-()
                     RETURN count(r) AS total_edge_count
                   $$) AS (total_edge_count integer)"""
        record = (await self._query(query))[0]
        if record:
            edge_count = int(record["total_edge_count"])
            return edge_count
        return 0

    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        """Get the total degree of two nodes."""
        src_degree = await self.node_degree(src_id)
        trg_degree = await self.node_degree(tgt_id)
        src_degree = 0 if src_degree is None else src_degree
        trg_degree = 0 if trg_degree is None else trg_degree
        return int(src_degree) + int(trg_degree)

    async def get_edge(self, source_node_id: str, target_node_id: str) -> dict[str, str] | None:
        """Get edge properties between two nodes."""
        src_label = self._normalize_node_id(source_node_id)
        tgt_label = self._normalize_node_id(target_node_id)

        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (a:base {{entity_id: "{src_label}"}})-[r]-(b:base {{entity_id: "{tgt_label}"}})
                     RETURN properties(r) as edge_properties
                     LIMIT 1
                   $$) AS (edge_properties agtype)"""
        record = await self._query(query)
        if record and record[0] and record[0]["edge_properties"]:
            result = record[0]["edge_properties"]

            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse edge string: {result}")

            return result
        return None

    async def get_node_edges(self, source_node_id: str) -> list[tuple[str, str]] | None:
        """Retrieve all edges for a particular node."""
        label = self._normalize_node_id(source_node_id)
        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                      MATCH (n:base {{entity_id: "{label}"}})
                      OPTIONAL MATCH (n)-[]-(connected:base)
                      RETURN n.entity_id AS source_id, connected.entity_id AS connected_id
                    $$) AS (source_id text, connected_id text)"""

        results = await self._query(query)
        edges = []
        for record in results:
            source_id = record["source_id"]
            connected_id = record["connected_id"]

            if source_id and connected_id:
                edges.append((source_id, connected_id))

        return edges

    async def upsert_node(self, node_id: str, node_data: dict[str, str]) -> None:
        """Upsert a node in the graph."""
        if "entity_id" not in node_data:
            raise ValueError("PostgreSQL: node properties must contain an 'entity_id' field")

        label = self._normalize_node_id(node_id)
        properties = self._format_properties(node_data)

        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MERGE (n:base {{entity_id: "{label}"}})
                     SET n += {properties}
                     RETURN n
                   $$) AS (n agtype)"""

        try:
            await self._query(query, readonly=False, upsert=True)
        except Exception:
            logger.error(f"POSTGRES, upsert_node error on node_id: `{node_id}`")
            raise

    async def upsert_edge(self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]) -> None:
        """Upsert an edge between two nodes."""
        src_label = self._normalize_node_id(source_node_id)
        tgt_label = self._normalize_node_id(target_node_id)
        edge_properties = self._format_properties(edge_data)

        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (source:base {{entity_id: "{src_label}"}})
                     WITH source
                     MATCH (target:base {{entity_id: "{tgt_label}"}})
                     MERGE (source)-[r:DIRECTED]-(target)
                     SET r += {edge_properties}
                     SET r += {edge_properties}
                     RETURN r
                   $$) AS (r agtype)"""

        try:
            await self._query(query, readonly=False, upsert=True)
        except Exception:
            logger.error(f"POSTGRES, upsert_edge error on edge: `{source_node_id}`-`{target_node_id}`")
            raise

    async def delete_node(self, node_id: str) -> None:
        """Delete a node from the graph."""
        label = self._normalize_node_id(node_id)
        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (n:base {{entity_id: "{label}"}})
                     DETACH DELETE n
                   $$) AS (n agtype)"""

        try:
            await self._query(query, readonly=False)
        except Exception as e:
            logger.error("Error during node deletion: {%s}", e)
            raise

    async def remove_nodes(self, node_ids: list[str]) -> None:
        """Remove multiple nodes from the graph."""
        node_ids = [self._normalize_node_id(node_id) for node_id in node_ids]
        node_id_list = ", ".join([f'"{node_id}"' for node_id in node_ids])

        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (n:base)
                     WHERE n.entity_id IN [{node_id_list}]
                     DETACH DELETE n
                   $$) AS (n agtype)"""

        try:
            await self._query(query, readonly=False)
        except Exception as e:
            logger.error("Error during node removal: {%s}", e)
            raise

    async def remove_edges(self, edges: list[tuple[str, str]]) -> None:
        """Remove multiple edges from the graph."""
        for source, target in edges:
            src_label = self._normalize_node_id(source)
            tgt_label = self._normalize_node_id(target)

            query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                         MATCH (a:base {{entity_id: "{src_label}"}})-[r]-(b:base {{entity_id: "{tgt_label}"}})
                         DELETE r
                       $$) AS (r agtype)"""

            try:
                await self._query(query, readonly=False)
                logger.debug(f"Deleted edge from '{source}' to '{target}'")
            except Exception as e:
                logger.error(f"Error during edge deletion: {str(e)}")
                raise

    # 为了简洁起见，我会实现一些基础的批量方法，更复杂的方法可以后续添加
    async def get_nodes_batch(self, node_ids: list[str]) -> dict[str, dict]:
        """Retrieve multiple nodes in one query."""
        if not node_ids:
            return {}

        formatted_ids = ", ".join(['"' + self._normalize_node_id(node_id) + '"' for node_id in node_ids])
        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     UNWIND [{formatted_ids}] AS node_id
                     MATCH (n:base {{entity_id: node_id}})
                     RETURN node_id, n
                   $$) AS (node_id text, n agtype)"""

        results = await self._query(query)
        nodes_dict = {}
        for result in results:
            if result["node_id"] and result["n"]:
                node_dict = result["n"]["properties"]

                if isinstance(node_dict, str):
                    try:
                        node_dict = json.loads(node_dict)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse node string in batch: {node_dict}")

                if "labels" in node_dict:
                    node_dict["labels"] = [label for label in node_dict["labels"] if label != "base"]
                nodes_dict[result["node_id"]] = node_dict

        return nodes_dict

    async def node_degrees_batch(self, node_ids: list[str]) -> dict[str, int]:
        """Retrieve the degree for multiple nodes."""
        if not node_ids:
            return {}

        formatted_ids = ", ".join(['"' + self._normalize_node_id(node_id) + '"' for node_id in node_ids])

        outgoing_query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     UNWIND [{formatted_ids}] AS node_id
                     MATCH (n:base {{entity_id: node_id}})
                     OPTIONAL MATCH (n)-[r]->(a)
                     RETURN node_id, count(a) AS out_degree
                   $$) AS (node_id text, out_degree bigint)"""

        incoming_query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     UNWIND [{formatted_ids}] AS node_id
                     MATCH (n:base {{entity_id: node_id}})
                     OPTIONAL MATCH (n)<-[r]-(b)
                     RETURN node_id, count(b) AS in_degree
                   $$) AS (node_id text, in_degree bigint)"""

        outgoing_results = await self._query(outgoing_query)
        incoming_results = await self._query(incoming_query)

        out_degrees = {}
        in_degrees = {}

        for result in outgoing_results:
            if result["node_id"] is not None:
                out_degrees[result["node_id"]] = int(result["out_degree"])

        for result in incoming_results:
            if result["node_id"] is not None:
                in_degrees[result["node_id"]] = int(result["in_degree"])

        degrees_dict = {}
        for node_id in node_ids:
            out_degree = out_degrees.get(node_id, 0)
            in_degree = in_degrees.get(node_id, 0)
            degrees_dict[node_id] = out_degree + in_degree

        return degrees_dict

    async def edge_degrees_batch(self, edges: list[tuple[str, str]]) -> dict[tuple[str, str], int]:
        """Calculate the combined degree for each edge."""
        if not edges:
            return {}

        all_nodes = set()
        for src, tgt in edges:
            all_nodes.add(src)
            all_nodes.add(tgt)

        node_degrees = await self.node_degrees_batch(list(all_nodes))

        edge_degrees_dict = {}
        for src, tgt in edges:
            src_degree = node_degrees.get(src, 0)
            tgt_degree = node_degrees.get(tgt, 0)
            edge_degrees_dict[(src, tgt)] = src_degree + tgt_degree

        return edge_degrees_dict

    async def get_edges_batch(self, pairs: list[dict[str, str]]) -> dict[tuple[str, str], dict]:
        """Retrieve edge properties for multiple pairs."""
        if not pairs:
            return {}

        # 简化实现，更复杂的批量查询可以后续添加
        edges_dict = {}
        for pair in pairs:
            src = pair["src"]
            tgt = pair["tgt"]
            edge_props = await self.get_edge(src, tgt)
            if edge_props:
                edges_dict[(src, tgt)] = edge_props

        return edges_dict

    async def get_nodes_edges_batch(self, node_ids: list[str]) -> dict[str, list[tuple[str, str]]]:
        """Get all edges for multiple nodes."""
        if not node_ids:
            return {}

        nodes_edges_dict = {node_id: [] for node_id in node_ids}
        
        # 简化实现
        for node_id in node_ids:
            edges = await self.get_node_edges(node_id)
            if edges:
                nodes_edges_dict[node_id] = edges

        return nodes_edges_dict

    async def get_all_labels(self) -> list[str]:
        """Get all labels in the graph."""
        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (n:base)
                     WHERE n.entity_id IS NOT NULL
                     RETURN DISTINCT n.entity_id AS label
                     ORDER BY n.entity_id
                   $$) AS (label text)"""

        results = await self._query(query)
        labels = []
        for result in results:
            if result and isinstance(result, dict) and "label" in result:
                labels.append(result["label"])
        return labels

    async def get_knowledge_graph(self, node_label: str, max_depth: int = 3, max_nodes: int = MAX_GRAPH_NODES):
        """Retrieve a connected subgraph."""
        # 简化实现，返回基本的知识图谱结构
        # 更复杂的BFS实现可以后续添加
        from aperag.graph.lightrag.types import KnowledgeGraph, KnowledgeGraphNode, KnowledgeGraphEdge
        
        kg = KnowledgeGraph()
        
        if node_label == "*":
            # 获取所有节点（限制数量）
            query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                    MATCH (n:base)
                    RETURN n
                    LIMIT {max_nodes}
                $$) AS (n agtype)"""
            
            results = await self._query(query)
            for result in results:
                if result.get("n"):
                    node_data = result["n"]
                    kg.nodes.append(KnowledgeGraphNode(
                        id=str(node_data["id"]),
                        labels=[node_data["properties"]["entity_id"]],
                        properties=node_data["properties"],
                    ))
        else:
            # 从特定节点开始的子图
            node = await self.get_node(node_label)
            if node:
                kg.nodes.append(KnowledgeGraphNode(
                    id=node_label,
                    labels=[node_label],
                    properties=node,
                ))
                
                edges = await self.get_node_edges(node_label)
                if edges:
                    for src, tgt in edges[:max_nodes]:
                        edge_props = await self.get_edge(src, tgt)
                        if edge_props:
                            kg.edges.append(KnowledgeGraphEdge(
                                id=f"{src}-{tgt}",
                                type="DIRECTED",
                                source=src,
                                target=tgt,
                                properties=edge_props,
                            ))

        return kg

    async def drop(self) -> dict[str, str]:
        """Drop the storage."""
        try:
            drop_query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                              MATCH (n)
                              DETACH DELETE n
                            $$) AS (result agtype)"""

            await self._query(drop_query, readonly=False)
            return {"status": "success", "message": "graph data dropped"}
        except Exception as e:
            logger.error(f"Error dropping graph: {e}")
            return {"status": "error", "message": str(e)} 


# Constants and SQL templates from the original postgres_impl.py

NAMESPACE_TABLE_MAP = {
    NameSpace.KV_STORE_FULL_DOCS: "LIGHTRAG_DOC_FULL",
    NameSpace.KV_STORE_TEXT_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
    NameSpace.VECTOR_STORE_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
    NameSpace.VECTOR_STORE_ENTITIES: "LIGHTRAG_VDB_ENTITY",
    NameSpace.VECTOR_STORE_RELATIONSHIPS: "LIGHTRAG_VDB_RELATION",
    NameSpace.DOC_STATUS: "LIGHTRAG_DOC_STATUS",
    NameSpace.KV_STORE_LLM_RESPONSE_CACHE: "LIGHTRAG_LLM_CACHE",
}


def namespace_to_table_name(namespace: str) -> str:
    """Map namespace to table name."""
    for k, v in NAMESPACE_TABLE_MAP.items():
        if is_namespace(namespace, k):
            return v
    return None


TABLES = {
    "LIGHTRAG_DOC_FULL": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_FULL (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    doc_name VARCHAR(1024),
                    content TEXT,
                    meta JSONB,
                    create_time TIMESTAMP(0),
                    update_time TIMESTAMP(0),
                    CONSTRAINT LIGHTRAG_DOC_FULL_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_DOC_CHUNKS": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_CHUNKS (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    full_doc_id VARCHAR(256),
                    chunk_order_index INTEGER,
                    tokens INTEGER,
                    content TEXT,
                    content_vector VECTOR,
                    file_path VARCHAR(256),
                    create_time TIMESTAMP(0) WITH TIME ZONE,
                    update_time TIMESTAMP(0) WITH TIME ZONE,
                    CONSTRAINT LIGHTRAG_DOC_CHUNKS_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_VDB_ENTITY": {
        "ddl": """CREATE TABLE LIGHTRAG_VDB_ENTITY (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    entity_name VARCHAR(255),
                    content TEXT,
                    content_vector VECTOR,
                    create_time TIMESTAMP(0) WITH TIME ZONE,
                    update_time TIMESTAMP(0) WITH TIME ZONE,
                    chunk_ids VARCHAR(255)[] NULL,
                    file_path TEXT NULL,
                    CONSTRAINT LIGHTRAG_VDB_ENTITY_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_VDB_RELATION": {
        "ddl": """CREATE TABLE LIGHTRAG_VDB_RELATION (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    source_id VARCHAR(256),
                    target_id VARCHAR(256),
                    content TEXT,
                    content_vector VECTOR,
                    create_time TIMESTAMP(0) WITH TIME ZONE,
                    update_time TIMESTAMP(0) WITH TIME ZONE,
                    chunk_ids VARCHAR(255)[] NULL,
                    file_path TEXT NULL,
                    CONSTRAINT LIGHTRAG_VDB_RELATION_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_LLM_CACHE": {
        "ddl": """CREATE TABLE LIGHTRAG_LLM_CACHE (
                    workspace varchar(255) NOT NULL,
                    id varchar(255) NOT NULL,
                    mode varchar(32) NOT NULL,
                    original_prompt TEXT,
                    return_value TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP,
                    CONSTRAINT LIGHTRAG_LLM_CACHE_PK PRIMARY KEY (workspace, mode, id)
                    )"""
    },
    "LIGHTRAG_DOC_STATUS": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_STATUS (
                   workspace varchar(255) NOT NULL,
                   id varchar(255) NOT NULL,
                   content TEXT NULL,
                   content_summary varchar(255) NULL,
                   content_length int4 NULL,
                   chunks_count int4 NULL,
                   status varchar(64) NULL,
                   file_path TEXT NULL,
                   created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NULL,
                   updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NULL,
                   CONSTRAINT LIGHTRAG_DOC_STATUS_PK PRIMARY KEY (workspace, id)
                  )"""
    },
}


SQL_TEMPLATES = {
    # SQL for KVStorage
    "get_by_id_full_docs": """SELECT id, COALESCE(content, '') as content
                                FROM LIGHTRAG_DOC_FULL WHERE workspace=%s AND id=%s
                            """,
    "get_by_id_text_chunks": """SELECT id, tokens, COALESCE(content, '') as content,
                                chunk_order_index, full_doc_id, file_path
                                FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=%s AND id=%s
                            """,
    "get_by_id_llm_response_cache": """SELECT id, original_prompt, COALESCE(return_value, '') as "return", mode
                                FROM LIGHTRAG_LLM_CACHE WHERE workspace=%s AND mode=%s
                               """,
    "get_by_mode_id_llm_response_cache": """SELECT id, original_prompt, COALESCE(return_value, '') as "return", mode
                           FROM LIGHTRAG_LLM_CACHE WHERE workspace=%s AND mode=%s AND id=%s
                          """,
    "get_by_ids_full_docs": """SELECT id, COALESCE(content, '') as content
                                 FROM LIGHTRAG_DOC_FULL WHERE workspace=%s AND id IN ({ids})
                            """,
    "get_by_ids_text_chunks": """SELECT id, tokens, COALESCE(content, '') as content,
                                  chunk_order_index, full_doc_id, file_path
                                   FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=%s AND id IN ({ids})
                                """,
    "get_by_ids_llm_response_cache": """SELECT id, original_prompt, COALESCE(return_value, '') as "return", mode
                                 FROM LIGHTRAG_LLM_CACHE WHERE workspace=%s AND mode IN ({ids})
                                """,
    "filter_keys": "SELECT id FROM {table_name} WHERE workspace=%s AND id IN ({ids})",
    "upsert_doc_full": """INSERT INTO LIGHTRAG_DOC_FULL (id, content, workspace)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (workspace,id) DO UPDATE
                           SET content = EXCLUDED.content, update_time = CURRENT_TIMESTAMP
                       """,
    "upsert_llm_response_cache": """INSERT INTO LIGHTRAG_LLM_CACHE(workspace,id,original_prompt,return_value,mode)
                                      VALUES (%s, %s, %s, %s, %s)
                                      ON CONFLICT (workspace,mode,id) DO UPDATE
                                      SET original_prompt = EXCLUDED.original_prompt,
                                      return_value=EXCLUDED.return_value,
                                      mode=EXCLUDED.mode,
                                      update_time = CURRENT_TIMESTAMP
                                     """,
    "upsert_chunk": """INSERT INTO LIGHTRAG_DOC_CHUNKS (workspace, id, tokens,
                      chunk_order_index, full_doc_id, content, content_vector, file_path,
                      create_time, update_time)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                      ON CONFLICT (workspace,id) DO UPDATE
                      SET tokens=EXCLUDED.tokens,
                      chunk_order_index=EXCLUDED.chunk_order_index,
                      full_doc_id=EXCLUDED.full_doc_id,
                      content = EXCLUDED.content,
                      content_vector=EXCLUDED.content_vector,
                      file_path=EXCLUDED.file_path,
                      update_time = EXCLUDED.update_time
                     """,
    # SQL for VectorStorage
    "upsert_entity": """INSERT INTO LIGHTRAG_VDB_ENTITY (workspace, id, entity_name, content,
                      content_vector, chunk_ids, file_path, create_time, update_time)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                      ON CONFLICT (workspace,id) DO UPDATE
                      SET entity_name=EXCLUDED.entity_name,
                      content=EXCLUDED.content,
                      content_vector=EXCLUDED.content_vector,
                      chunk_ids=EXCLUDED.chunk_ids,
                      file_path=EXCLUDED.file_path,
                      update_time=EXCLUDED.update_time
                     """,
    "upsert_relationship": """INSERT INTO LIGHTRAG_VDB_RELATION (workspace, id, source_id,
                      target_id, content, content_vector, chunk_ids, file_path, create_time, update_time)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                      ON CONFLICT (workspace,id) DO UPDATE
                      SET source_id=EXCLUDED.source_id,
                      target_id=EXCLUDED.target_id,
                      content=EXCLUDED.content,
                      content_vector=EXCLUDED.content_vector,
                      chunk_ids=EXCLUDED.chunk_ids,
                      file_path=EXCLUDED.file_path,
                      update_time = EXCLUDED.update_time
                     """,
    "relationships": """
    WITH relevant_chunks AS (
        SELECT id as chunk_id
        FROM LIGHTRAG_DOC_CHUNKS
        WHERE %s IS NULL OR full_doc_id = ANY(%s)
    )
    SELECT source_id as src_id, target_id as tgt_id, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at
    FROM (
        SELECT r.id, r.source_id, r.target_id, r.create_time, 1 - (r.content_vector <=> '[{embedding_string}]'::vector) as distance
        FROM LIGHTRAG_VDB_RELATION r
        JOIN relevant_chunks c ON c.chunk_id = ANY(r.chunk_ids)
        WHERE r.workspace=%s
    ) filtered
    WHERE distance>%s
    ORDER BY distance DESC
    LIMIT %s
    """,
    "entities": """
        WITH relevant_chunks AS (
            SELECT id as chunk_id
            FROM LIGHTRAG_DOC_CHUNKS
            WHERE %s IS NULL OR full_doc_id = ANY(%s)
        )
        SELECT entity_name, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM
            (
                SELECT e.id, e.entity_name, e.create_time, 1 - (e.content_vector <=> '[{embedding_string}]'::vector) as distance
                FROM LIGHTRAG_VDB_ENTITY e
                JOIN relevant_chunks c ON c.chunk_id = ANY(e.chunk_ids)
                WHERE e.workspace=%s
            ) as chunk_distances
            WHERE distance>%s
            ORDER BY distance DESC
            LIMIT %s
    """,
    "chunks": """
        WITH relevant_chunks AS (
            SELECT id as chunk_id
            FROM LIGHTRAG_DOC_CHUNKS
            WHERE %s IS NULL OR full_doc_id = ANY(%s)
        )
        SELECT id, content, file_path, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM
            (
                SELECT id, content, file_path, create_time, 1 - (content_vector <=> '[{embedding_string}]'::vector) as distance
                FROM LIGHTRAG_DOC_CHUNKS
                WHERE workspace=%s
                AND id IN (SELECT chunk_id FROM relevant_chunks)
            ) as chunk_distances
            WHERE distance>%s
            ORDER BY distance DESC
            LIMIT %s
    """,
    # DROP tables
    "drop_specifiy_table_workspace": """
        DELETE FROM {table_name} WHERE workspace=%s
       """,
} 