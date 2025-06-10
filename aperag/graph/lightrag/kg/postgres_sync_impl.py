import asyncio
import datetime
import json
import os
from dataclasses import dataclass, field
from datetime import timezone
from typing import Any, Union, final

import numpy as np
from ..base import (
    BaseKVStorage,
    BaseVectorStorage,
    DocProcessingStatus,
    DocStatus,
    DocStatusStorage,
)
from ..namespace import NameSpace, is_namespace
from ..utils import logger

from dotenv import load_dotenv

# Import sync connection manager
try:
    from aperag.db.postgres_sync_manager import PostgreSQLSyncConnectionManager
except ImportError:
    PostgreSQLSyncConnectionManager = None

# use the .env that is inside the current folder
# allows to use different .env file for each lightrag instance
# the OS environment variables take precedence over the .env file
load_dotenv(dotenv_path=".env", override=False)

# Get maximum number of graph nodes from environment variable, default is 1000
MAX_GRAPH_NODES = int(os.getenv("MAX_GRAPH_NODES", 1000))


@final
@dataclass
class PGSyncKVStorage(BaseKVStorage):
    """PostgreSQL KV Storage using sync driver with async interface."""
    
    def __post_init__(self):
        self._max_batch_size = int(os.getenv("EMBEDDING_BATCH_NUM", 32))

    async def initialize(self):
        """Initialize storage and prepare workspace."""
        if PostgreSQLSyncConnectionManager is None:
            raise RuntimeError("PostgreSQL sync connection manager is not available")
        
        # Initialize in thread to avoid blocking
        await asyncio.to_thread(PostgreSQLSyncConnectionManager.initialize)
        logger.info(f"PGSyncKVStorage initialized for workspace '{self.workspace}'")

    async def finalize(self):
        """Clean up resources."""
        # Nothing to clean up - connection managed at worker level
        logger.debug(f"PGSyncKVStorage finalized for workspace '{self.workspace}'")

    async def get_all(self) -> dict[str, Any]:
        """Get all data from storage"""
        def _sync_get_all():
            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                logger.error(f"Unknown namespace for get_all: {self.namespace}")
                return {}

            sql = f"SELECT * FROM {table_name} WHERE workspace=%s"
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (self.workspace,), fetch_all=True
            )
            return {row["id"]: row for row in results}
        
        return await asyncio.to_thread(_sync_get_all)

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get doc_full data by id."""
        def _sync_get_by_id():
            sql_key = f"get_by_id_{self.storage_type}"
            sql = SQL_TEMPLATES[sql_key]
            result = PostgreSQLSyncConnectionManager.execute_query(
                sql, (self.workspace, id), fetch_one=True
            )
            return result
        
        return await asyncio.to_thread(_sync_get_by_id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get doc_chunks data by id"""
        def _sync_get_by_ids():
            if not ids:
                return []
            # Build IN clause with placeholders
            placeholders = ",".join(["%s"] * len(ids))
            sql_key = f"get_by_ids_{self.storage_type}"
            sql = SQL_TEMPLATES[sql_key].format(ids=placeholders)
            
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (self.workspace, *ids), fetch_all=True
            )
            return results
        
        return await asyncio.to_thread(_sync_get_by_ids)

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out duplicated content"""
        def _sync_filter_keys():
            if not keys:
                return set()
            table_name = namespace_to_table_name(self.namespace)
            # Build IN clause with placeholders
            placeholders = ",".join(["%s"] * len(keys))
            sql = f"SELECT id FROM {table_name} WHERE workspace=%s AND id IN ({placeholders})"
            
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (self.workspace, *list(keys)), fetch_all=True
            )
            
            exist_keys = [row["id"] for row in results]
            new_keys = set([s for s in keys if s not in exist_keys])
            return new_keys
        
        return await asyncio.to_thread(_sync_filter_keys)

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Insert or update data"""
        def _sync_upsert():
            logger.debug(f"Inserting {len(data)} to {self.namespace}")
            if not data:
                return

            if is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                # Handle text chunks if needed
                pass
            elif is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                upsert_sql = SQL_TEMPLATES["upsert_doc_full"]
                for k, v in data.items():
                    PostgreSQLSyncConnectionManager.execute_query(
                        upsert_sql, (k, v["content"], self.workspace)
                    )
        
        await asyncio.to_thread(_sync_upsert)

    async def delete(self, ids: list[str]) -> None:
        """Delete specific records from storage by their IDs"""
        def _sync_delete():
            if not ids:
                return

            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                logger.error(f"Unknown namespace for deletion: {self.namespace}")
                return

            # Use ANY for PostgreSQL array operations
            sql = f"DELETE FROM {table_name} WHERE workspace=%s AND id = ANY(%s)"
            PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, ids))
            logger.debug(f"Successfully deleted {len(ids)} records from {self.namespace}")
        
        await asyncio.to_thread(_sync_delete)

    async def drop(self) -> dict[str, str]:
        """Drop the storage"""
        def _sync_drop():
            try:
                table_name = namespace_to_table_name(self.namespace)
                if not table_name:
                    return {
                        "status": "error",
                        "message": f"Unknown namespace: {self.namespace}",
                    }

                sql = f"DELETE FROM {table_name} WHERE workspace=%s"
                PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace,))
                return {"status": "success", "message": "data dropped"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        return await asyncio.to_thread(_sync_drop)


@final
@dataclass
class PGSyncVectorStorage(BaseVectorStorage):
    """PostgreSQL Vector Storage using sync driver with async interface."""
    
    def __post_init__(self):
        self._max_batch_size = int(os.getenv("EMBEDDING_BATCH_NUM", 32))
        self.cosine_better_than_threshold = float(os.getenv("COSINE_THRESHOLD", 0.2))

    async def initialize(self):
        """Initialize storage and prepare workspace."""
        if PostgreSQLSyncConnectionManager is None:
            raise RuntimeError("PostgreSQL sync connection manager is not available")
        
        await asyncio.to_thread(PostgreSQLSyncConnectionManager.initialize)
        logger.info(f"PGSyncVectorStorage initialized for workspace '{self.workspace}'")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGSyncVectorStorage finalized for workspace '{self.workspace}'")

    def _prepare_upsert_data(self, item: dict[str, Any], current_time: datetime.datetime) -> tuple[str, tuple]:
        """Prepare upsert SQL and data based on namespace."""
        if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
            sql = SQL_TEMPLATES["upsert_chunk"]
            data = (
                self.workspace, item["__id__"], item["tokens"],
                item["chunk_order_index"], item["full_doc_id"], item["content"],
                json.dumps(item["__vector__"].tolist()), item["file_path"],
                current_time, current_time
            )
        elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
            source_id = item["source_id"]
            chunk_ids = source_id.split("<SEP>") if isinstance(source_id, str) and "<SEP>" in source_id else [source_id]
            sql = SQL_TEMPLATES["upsert_entity"]
            data = (
                self.workspace, item["__id__"], item["entity_name"], item["content"],
                json.dumps(item["__vector__"].tolist()), chunk_ids, 
                item.get("file_path"), current_time, current_time
            )
        elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
            source_id = item["source_id"]
            chunk_ids = source_id.split("<SEP>") if isinstance(source_id, str) and "<SEP>" in source_id else [source_id]
            sql = SQL_TEMPLATES["upsert_relationship"]
            data = (
                self.workspace, item["__id__"], item["src_id"], item["tgt_id"], item["content"],
                json.dumps(item["__vector__"].tolist()), chunk_ids,
                item.get("file_path"), current_time, current_time
            )
        else:
            raise ValueError(f"{self.namespace} is not supported")
        
        return sql, data

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Insert or update vector data"""
        logger.debug(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        # Get current time with UTC timezone
        current_time = datetime.datetime.now(timezone.utc)
        list_data = [
            {
                "__id__": k,
                **{k1: v1 for k1, v1 in v.items()},
            }
            for k, v in data.items()
        ]
        
        # Compute embeddings first (async)
        contents = [v["content"] for v in data.values()]
        batches = [
            contents[i : i + self._max_batch_size]
            for i in range(0, len(contents), self._max_batch_size)
        ]

        embedding_tasks = [self.embedding_func(batch) for batch in batches]
        embeddings_list = await asyncio.gather(*embedding_tasks)
        embeddings = np.concatenate(embeddings_list)
        
        for i, d in enumerate(list_data):
            d["__vector__"] = embeddings[i]
        
        # Now perform sync upsert
        def _sync_upsert_with_vectors():
            for item in list_data:
                sql, params = self._prepare_upsert_data(item, current_time)
                PostgreSQLSyncConnectionManager.execute_query(sql, params)
        
        await asyncio.to_thread(_sync_upsert_with_vectors)

    async def query(self, query: str, top_k: int, ids: list[str] | None = None) -> list[dict[str, Any]]:
        """Query vectors by similarity"""
        # Compute embedding for query
        embeddings = await self.embedding_func([query])
        embedding = embeddings[0]
        embedding_string = ",".join(map(str, embedding))
        
        def _sync_query():
            sql = SQL_TEMPLATES[self.storage_type].format(embedding_string=embedding_string)
            params = (self.workspace, ids, self.cosine_better_than_threshold, top_k)
            results = PostgreSQLSyncConnectionManager.execute_query(sql, params, fetch_all=True)
            return results
        
        return await asyncio.to_thread(_sync_query)

    async def delete(self, ids: list[str]) -> None:
        """Delete vectors with specified IDs from the storage."""
        def _sync_delete():
            if not ids:
                return

            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                logger.error(f"Unknown namespace for vector deletion: {self.namespace}")
                return

            sql = f"DELETE FROM {table_name} WHERE workspace=%s AND id = ANY(%s)"
            PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, ids))
            logger.debug(f"Successfully deleted {len(ids)} vectors from {self.namespace}")
        
        await asyncio.to_thread(_sync_delete)

    async def delete_entity(self, entity_name: str) -> None:
        """Delete an entity by its name from the vector storage."""
        def _sync_delete_entity():
            sql = "DELETE FROM LIGHTRAG_VDB_ENTITY WHERE workspace=%s AND entity_name=%s"
            PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, entity_name))
            logger.debug(f"Successfully deleted entity {entity_name}")
        
        await asyncio.to_thread(_sync_delete_entity)

    async def delete_entity_relation(self, entity_name: str) -> None:
        """Delete all relations associated with an entity."""
        def _sync_delete_entity_relation():
            sql = "DELETE FROM LIGHTRAG_VDB_RELATION WHERE workspace=%s AND (source_id=%s OR target_id=%s)"
            PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, entity_name, entity_name))
            logger.debug(f"Successfully deleted relations for entity {entity_name}")
        
        await asyncio.to_thread(_sync_delete_entity_relation)

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get vector data by its ID"""
        def _sync_get_by_id():
            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                logger.error(f"Unknown namespace for ID lookup: {self.namespace}")
                return None

            sql = f"SELECT *, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM {table_name} WHERE workspace=%s AND id=%s"
            result = PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, id), fetch_one=True)
            return result
        
        return await asyncio.to_thread(_sync_get_by_id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get multiple vector data by their IDs"""
        def _sync_get_by_ids():
            if not ids:
                return []

            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                logger.error(f"Unknown namespace for IDs lookup: {self.namespace}")
                return []

            placeholders = ",".join(["%s"] * len(ids))
            sql = f"SELECT *, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM {table_name} WHERE workspace=%s AND id IN ({placeholders})"
            results = PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, *ids), fetch_all=True)
            return results
        
        return await asyncio.to_thread(_sync_get_by_ids)

    async def drop(self) -> dict[str, str]:
        """Drop the storage"""
        def _sync_drop():
            try:
                table_name = namespace_to_table_name(self.namespace)
                if not table_name:
                    return {
                        "status": "error",
                        "message": f"Unknown namespace: {self.namespace}",
                    }

                sql = f"DELETE FROM {table_name} WHERE workspace=%s"
                PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace,))
                return {"status": "success", "message": "data dropped"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        return await asyncio.to_thread(_sync_drop)


@final
@dataclass
class PGSyncDocStatusStorage(DocStatusStorage):
    """PostgreSQL Document Status Storage using sync driver with async interface."""
    
    async def initialize(self):
        """Initialize storage and prepare workspace."""
        if PostgreSQLSyncConnectionManager is None:
            raise RuntimeError("PostgreSQL sync connection manager is not available")
        
        await asyncio.to_thread(PostgreSQLSyncConnectionManager.initialize)

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGSyncDocStatusStorage finalized for workspace '{self.workspace}'")

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out duplicated content"""
        def _sync_filter_keys():
            if not keys:
                return set()
            table_name = namespace_to_table_name(self.namespace)
            placeholders = ",".join(["%s"] * len(keys))
            sql = f"SELECT id FROM {table_name} WHERE workspace=%s AND id IN ({placeholders})"
            
            results = PostgreSQLSyncConnectionManager.execute_query(
                sql, (self.workspace, *list(keys)), fetch_all=True
            )
            
            exist_keys = [row["id"] for row in results]
            new_keys = set([s for s in keys if s not in exist_keys])
            print(f"keys: {keys}")
            print(f"new_keys: {new_keys}")
            return new_keys
        
        return await asyncio.to_thread(_sync_filter_keys)

    async def get_by_id(self, id: str) -> Union[dict[str, Any], None]:
        def _sync_get_by_id():
            sql = "SELECT * FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s AND id=%s"
            result = PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, id), fetch_one=True)
            
            if not result:
                return None
            
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
        
        return await asyncio.to_thread(_sync_get_by_id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get doc_chunks data by multiple IDs."""
        def _sync_get_by_ids():
            if not ids:
                return []

            placeholders = ",".join(["%s"] * len(ids))
            sql = f"SELECT * FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s AND id IN ({placeholders})"
            results = PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, *ids), fetch_all=True)

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
        """Get counts of documents in each status"""
        def _sync_get_status_counts():
            sql = 'SELECT status, COUNT(1) as count FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s GROUP BY status'
            results = PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace,), fetch_all=True)
            
            counts = {}
            for row in results:
                counts[row["status"]] = row["count"]
            return counts
        
        return await asyncio.to_thread(_sync_get_status_counts)

    async def get_docs_by_status(self, status: DocStatus) -> dict[str, DocProcessingStatus]:
        """Get all documents with a specific status"""
        def _sync_get_docs_by_status():
            sql = "SELECT * FROM LIGHTRAG_DOC_STATUS WHERE workspace=%s AND status=%s"
            results = PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, status.value), fetch_all=True)
            
            docs_by_status = {
                row["id"]: DocProcessingStatus(
                    content=row["content"],
                    content_summary=row["content_summary"],
                    content_length=row["content_length"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    chunks_count=row["chunks_count"],
                    file_path=row["file_path"],
                )
                for row in results
            }
            return docs_by_status
        
        return await asyncio.to_thread(_sync_get_docs_by_status)

    async def delete(self, ids: list[str]) -> None:
        """Delete specific records from storage by their IDs"""
        def _sync_delete():
            if not ids:
                return

            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                logger.error(f"Unknown namespace for deletion: {self.namespace}")
                return

            sql = f"DELETE FROM {table_name} WHERE workspace=%s AND id = ANY(%s)"
            PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace, ids))
            logger.debug(f"Successfully deleted {len(ids)} records from {self.namespace}")
        
        await asyncio.to_thread(_sync_delete)

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Update or insert document status"""
        def _sync_upsert():
            logger.debug(f"Inserting {len(data)} to {self.namespace}")
            if not data:
                return

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
                created_at = parse_datetime(v.get("created_at"))
                updated_at = parse_datetime(v.get("updated_at"))

                PostgreSQLSyncConnectionManager.execute_query(
                    sql,
                    (
                        self.workspace, k, v["content"], v["content_summary"],
                        v["content_length"], v.get("chunks_count", -1),
                        v["status"], v["file_path"],
                        created_at, updated_at
                    )
                )
        
        await asyncio.to_thread(_sync_upsert)

    async def drop(self) -> dict[str, str]:
        """Drop the storage"""
        def _sync_drop():
            try:
                table_name = namespace_to_table_name(self.namespace)
                if not table_name:
                    return {
                        "status": "error",
                        "message": f"Unknown namespace: {self.namespace}",
                    }

                sql = f"DELETE FROM {table_name} WHERE workspace=%s"
                PostgreSQLSyncConnectionManager.execute_query(sql, (self.workspace,))
                return {"status": "success", "message": "data dropped"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        return await asyncio.to_thread(_sync_drop)


# Keep existing helper functions and update SQL templates
NAMESPACE_TABLE_MAP = {
    NameSpace.KV_STORE_FULL_DOCS: "LIGHTRAG_DOC_FULL",
    NameSpace.KV_STORE_TEXT_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
    NameSpace.VECTOR_STORE_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
    NameSpace.VECTOR_STORE_ENTITIES: "LIGHTRAG_VDB_ENTITY",
    NameSpace.VECTOR_STORE_RELATIONSHIPS: "LIGHTRAG_VDB_RELATION",
    NameSpace.DOC_STATUS: "LIGHTRAG_DOC_STATUS",
}


def namespace_to_table_name(namespace: str) -> str:
    for k, v in NAMESPACE_TABLE_MAP.items():
        if is_namespace(namespace, k):
            return v


SQL_TEMPLATES = {
    # SQL for KVStorage - updated to use %s instead of $1, $2
    "get_by_id_full_docs": """SELECT id, COALESCE(content, '') as content
                                FROM LIGHTRAG_DOC_FULL WHERE workspace=%s AND id=%s
                            """,
    "get_by_id_text_chunks": """SELECT id, tokens, COALESCE(content, '') as content,
                                chunk_order_index, full_doc_id, file_path
                                FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=%s AND id=%s
                            """,
    "get_by_ids_full_docs": """SELECT id, COALESCE(content, '') as content
                                 FROM LIGHTRAG_DOC_FULL WHERE workspace=%s AND id IN ({ids})
                            """,
    "get_by_ids_text_chunks": """SELECT id, tokens, COALESCE(content, '') as content,
                                  chunk_order_index, full_doc_id, file_path
                                   FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=%s AND id IN ({ids})
                                """,
    "upsert_doc_full": """INSERT INTO LIGHTRAG_DOC_FULL (id, content, workspace)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (workspace,id) DO UPDATE
                           SET content = EXCLUDED.content, update_time = CURRENT_TIMESTAMP
                       """,
    "upsert_chunk": """INSERT INTO LIGHTRAG_DOC_CHUNKS (workspace, id, tokens,
                      chunk_order_index, full_doc_id, content, content_vector, file_path,
                      create_time, update_time)
                      VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s, %s, %s)
                      ON CONFLICT (workspace,id) DO UPDATE
                      SET tokens=EXCLUDED.tokens,
                      chunk_order_index=EXCLUDED.chunk_order_index,
                      full_doc_id=EXCLUDED.full_doc_id,
                      content = EXCLUDED.content,
                      content_vector=EXCLUDED.content_vector,
                      file_path=EXCLUDED.file_path,
                      update_time = EXCLUDED.update_time
                     """,
    # SQL for VectorStorage - updated to use %s
    "upsert_entity": """INSERT INTO LIGHTRAG_VDB_ENTITY (workspace, id, entity_name, content,
                      content_vector, chunk_ids, file_path, create_time, update_time)
                      VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s, %s)
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
                      VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s)
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


@final
@dataclass 
class PGOpsDocStatusStorage(DocStatusStorage):
    """PostgreSQL Document Status Storage using DatabaseOps with sync interface."""
    
    async def initialize(self):
        """Initialize storage."""
        logger.info(f"PGOpsDocStatusStorage initialized for workspace '{self.workspace}'")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGOpsDocStatusStorage finalized for workspace '{self.workspace}'")

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out existing keys - not commonly used, return all as new"""
        # This method is not commonly used in LightRAG, so we return all keys as new
        return keys

    async def get_by_id(self, id: str) -> Union[dict[str, Any], None]:
        """Get document status by id"""
        def _sync_get_by_id():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            
            # Use the DatabaseOps method
            model = db_ops.query_lightrag_doc_status_by_id(self.workspace, id)
            if not model:
                return None
                
            # Convert to the expected format
            return {
                "content": model.content or "",
                "content_length": model.content_length or 0,
                "content_summary": model.content_summary or "",
                "status": model.status.value if model.status else "pending",
                "chunks_count": model.chunks_count,
                "created_at": model.created_at.isoformat() if model.created_at else "",
                "updated_at": model.updated_at.isoformat() if model.updated_at else "",
                "file_path": model.file_path or "",
            }

        return await asyncio.to_thread(_sync_get_by_id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get document status by ids - not used in the 4 core functions"""
        return []

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Update or insert document status"""
        def _sync_upsert():
            logger.debug(f"Inserting {len(data)} to {self.namespace}")
            if not data:
                return

            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            
            # Use the DatabaseOps method
            db_ops.upsert_lightrag_doc_status(self.workspace, data)

        await asyncio.to_thread(_sync_upsert)

    async def get_docs_by_status(self, status: DocStatus) -> dict[str, DocProcessingStatus]:
        """Get all documents with a specific status"""
        def _sync_get_docs_by_status():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.db.models import LightRAGDocStatus
            
            # Convert DocStatus to LightRAGDocStatus
            lightrag_status = LightRAGDocStatus(status.value)
            
            # Use the DatabaseOps method
            db_models = db_ops.query_lightrag_docs_by_status(self.workspace, lightrag_status)
            
            # Convert to DocProcessingStatus objects
            docs_by_status = {}
            for doc_id, model in db_models.items():
                docs_by_status[doc_id] = DocProcessingStatus(
                    content=model.content or "",
                    content_summary=model.content_summary or "",
                    content_length=model.content_length or 0,
                    status=DocStatus(model.status.value) if model.status else DocStatus.PENDING,
                    created_at=model.created_at.isoformat() if model.created_at else "",
                    updated_at=model.updated_at.isoformat() if model.updated_at else "",
                    chunks_count=model.chunks_count,
                    file_path=model.file_path or "",
                )
            
            return docs_by_status

        return await asyncio.to_thread(_sync_get_docs_by_status)

    async def delete(self, ids: list[str]) -> None:
        """Delete specific records from storage by their IDs"""
        def _sync_delete():
            if not ids:
                return

            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            
            # Use the DatabaseOps method
            deleted_count = db_ops.delete_lightrag_doc_status(self.workspace, ids)
            logger.debug(f"Successfully deleted {deleted_count} records from {self.namespace}")

        await asyncio.to_thread(_sync_delete)

    async def drop(self) -> dict[str, str]:
        """Drop the storage - not implemented for safety"""
        return {"status": "error", "message": "Drop operation not supported for database-backed storage"} 


@final
@dataclass 
class PGOpsSyncKVStorage(BaseKVStorage):
    """PostgreSQL KV Storage using DatabaseOps with sync interface."""
    
    async def initialize(self):
        """Initialize storage."""
        logger.info(f"PGOpsSyncKVStorage initialized for workspace '{self.workspace}'")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGOpsSyncKVStorage finalized for workspace '{self.workspace}'")

    async def get_all(self) -> dict[str, Any]:
        """Get all data from storage"""
        def _sync_get_all():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace
            
            # Determine which table to query based on namespace
            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                models = db_ops.query_lightrag_doc_full_all(self.workspace)
                return {doc_id: {"id": doc_id, "content": model.content or ""} for doc_id, model in models.items()}
            elif is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                models = db_ops.query_lightrag_doc_chunks_all(self.workspace)
                return {
                    chunk_id: {
                        "id": chunk_id,
                        "tokens": model.tokens,
                        "content": model.content or "",
                        "chunk_order_index": model.chunk_order_index,
                        "full_doc_id": model.full_doc_id,
                        "content_vector": model.content_vector,  # Now returns list[float] directly
                        "file_path": model.file_path
                    } for chunk_id, model in models.items()
                }
            else:
                logger.error(f"Unknown namespace for get_all: {self.namespace}")
                return {}

        return await asyncio.to_thread(_sync_get_all)

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get data by id"""
        def _sync_get_by_id():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace
            
            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                model = db_ops.query_lightrag_doc_full_by_id(self.workspace, id)
                if not model:
                    return None
                return {"id": model.id, "content": model.content or ""}
            elif is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                model = db_ops.query_lightrag_doc_chunks_by_id(self.workspace, id)
                if not model:
                    return None
                return {
                    "id": model.id,
                    "tokens": model.tokens,
                    "content": model.content or "",
                    "chunk_order_index": model.chunk_order_index,
                    "full_doc_id": model.full_doc_id,
                    "content_vector": model.content_vector,  # Now returns list[float] directly
                    "file_path": model.file_path
                }
            else:
                logger.error(f"Unknown namespace for get_by_id: {self.namespace}")
                return None

        return await asyncio.to_thread(_sync_get_by_id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get data by ids"""
        def _sync_get_by_ids():
            if not ids:
                return []
                
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace
            
            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                models = db_ops.query_lightrag_doc_full_by_ids(self.workspace, ids)
                return [{"id": model.id, "content": model.content or ""} for model in models]
            elif is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                models = db_ops.query_lightrag_doc_chunks_by_ids(self.workspace, ids)
                return [
                    {
                        "id": model.id,
                        "tokens": model.tokens,
                        "content": model.content or "",
                        "chunk_order_index": model.chunk_order_index,
                        "full_doc_id": model.full_doc_id,
                        "content_vector": model.content_vector,  # Now returns list[float] directly
                        "file_path": model.file_path
                    } for model in models
                ]
            else:
                logger.error(f"Unknown namespace for get_by_ids: {self.namespace}")
                return []

        return await asyncio.to_thread(_sync_get_by_ids)

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out existing keys"""
        def _sync_filter_keys():
            if not keys:
                return set()
                
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace
            
            keys_list = list(keys)
            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                existing_keys = db_ops.filter_lightrag_doc_full_keys(self.workspace, keys_list)
            elif is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                existing_keys = db_ops.filter_lightrag_doc_chunks_keys(self.workspace, keys_list)
            else:
                logger.error(f"Unknown namespace for filter_keys: {self.namespace}")
                return keys
            
            new_keys = set([s for s in keys if s not in existing_keys])
            return new_keys

        return await asyncio.to_thread(_sync_filter_keys)

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Insert or update data"""
        def _sync_upsert():
            logger.debug(f"Inserting {len(data)} to {self.namespace}")
            if not data:
                return

            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace

            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                # Transform data for doc_full format
                doc_data = {doc_id: {"content": doc_info.get("content", "")} for doc_id, doc_info in data.items()}
                db_ops.upsert_lightrag_doc_full(self.workspace, doc_data)
            elif is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                # Use data directly for chunks
                db_ops.upsert_lightrag_doc_chunks(self.workspace, data)
            else:
                logger.error(f"Unknown namespace for upsert: {self.namespace}")

        await asyncio.to_thread(_sync_upsert)

    async def delete(self, ids: list[str]) -> None:
        """Delete specific records from storage by their IDs"""
        def _sync_delete():
            if not ids:
                return

            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace

            if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
                deleted_count = db_ops.delete_lightrag_doc_full(self.workspace, ids)
                logger.debug(f"Successfully deleted {deleted_count} records from {self.namespace}")
            elif is_namespace(self.namespace, NameSpace.KV_STORE_TEXT_CHUNKS):
                deleted_count = db_ops.delete_lightrag_doc_chunks(self.workspace, ids)
                logger.debug(f"Successfully deleted {deleted_count} records from {self.namespace}")
            else:
                logger.error(f"Unknown namespace for deletion: {self.namespace}")

        await asyncio.to_thread(_sync_delete)

    async def drop(self) -> dict[str, str]:
        """Drop the storage - not implemented for safety"""
        return {"status": "error", "message": "Drop operation not supported for database-backed storage"} 


@final
@dataclass 
class PGOpsSyncVectorStorage(BaseVectorStorage):
    """PostgreSQL Vector Storage using DatabaseOps with sync interface."""
    
    def __post_init__(self):
        self._max_batch_size = int(os.getenv("EMBEDDING_BATCH_NUM", 32))
        self.cosine_better_than_threshold = float(os.getenv("COSINE_THRESHOLD", 0.2))

    async def initialize(self):
        """Initialize storage."""
        logger.info(f"PGOpsSyncVectorStorage initialized for workspace '{self.workspace}'")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGOpsSyncVectorStorage finalized for workspace '{self.workspace}'")

    def _prepare_vector_data(self, item: dict[str, Any], current_time: datetime.datetime) -> dict[str, Any]:
        """Prepare vector data based on namespace."""
        from aperag.graph.lightrag.namespace import NameSpace, is_namespace
        
        if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
            return {
                "tokens": item["tokens"],
                "chunk_order_index": item["chunk_order_index"],
                "full_doc_id": item["full_doc_id"],
                "content": item["content"],
                "content_vector": item["__vector__"].tolist() if hasattr(item["__vector__"], 'tolist') else item["__vector__"],
                "file_path": item.get("file_path"),
            }
        elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
            source_id = item["source_id"]
            chunk_ids = source_id.split("<SEP>") if isinstance(source_id, str) and "<SEP>" in source_id else [source_id]
            return {
                "entity_name": item["entity_name"],
                "content": item["content"],
                "content_vector": item["__vector__"].tolist() if hasattr(item["__vector__"], 'tolist') else item["__vector__"],
                "chunk_ids": chunk_ids,
                "file_path": item.get("file_path"),
            }
        elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
            source_id = item["source_id"]
            chunk_ids = source_id.split("<SEP>") if isinstance(source_id, str) and "<SEP>" in source_id else [source_id]
            return {
                "source_id": item["src_id"],
                "target_id": item["tgt_id"],
                "content": item["content"],
                "content_vector": item["__vector__"].tolist() if hasattr(item["__vector__"], 'tolist') else item["__vector__"],
                "chunk_ids": chunk_ids,
                "file_path": item.get("file_path"),
            }
        else:
            raise ValueError(f"{self.namespace} is not supported")

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Insert or update vector data"""
        logger.debug(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        # Get current time with UTC timezone
        current_time = datetime.datetime.now(timezone.utc)
        list_data = [
            {
                "__id__": k,
                **{k1: v1 for k1, v1 in v.items()},
            }
            for k, v in data.items()
        ]
        
        # Compute embeddings first (async)
        contents = [v["content"] for v in data.values()]
        batches = [
            contents[i : i + self._max_batch_size]
            for i in range(0, len(contents), self._max_batch_size)
        ]

        embedding_tasks = [self.embedding_func(batch) for batch in batches]
        embeddings_list = await asyncio.gather(*embedding_tasks)
        embeddings = np.concatenate(embeddings_list)
        
        for i, d in enumerate(list_data):
            d["__vector__"] = embeddings[i]

        def _sync_upsert_with_vectors():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace
            
            # Prepare data for each item
            vector_data = {}
            for item in list_data:
                item_id = item["__id__"]
                prepared_data = self._prepare_vector_data(item, current_time)
                vector_data[item_id] = prepared_data
            
            # Use appropriate DatabaseOps method based on namespace
            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                db_ops.upsert_lightrag_doc_chunks(self.workspace, vector_data)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                db_ops.upsert_lightrag_vdb_entity(self.workspace, vector_data)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                db_ops.upsert_lightrag_vdb_relation(self.workspace, vector_data)
            else:
                raise ValueError(f"{self.namespace} is not supported")
        
        await asyncio.to_thread(_sync_upsert_with_vectors)

    async def query(self, query: str, top_k: int, ids: list[str] | None = None) -> list[dict[str, Any]]:
        """Query vectors by similarity"""
        # Compute embedding for query
        embeddings = await self.embedding_func([query])
        embedding = embeddings[0]

        def _sync_query():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace
            
            # For now, return empty list as we need to implement vector similarity search in DatabaseOps
            # This would require adding vector similarity query methods to db_ops
            logger.warning(f"Vector similarity query not yet implemented for DatabaseOps-based storage")
            return []
        
        return await asyncio.to_thread(_sync_query)

    async def delete(self, ids: list[str]) -> None:
        """Delete vectors with specified IDs from the storage."""
        def _sync_delete():
            if not ids:
                return

            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace

            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                deleted_count = db_ops.delete_lightrag_doc_chunks(self.workspace, ids)
                logger.debug(f"Successfully deleted {deleted_count} vectors from {self.namespace}")
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                deleted_count = db_ops.delete_lightrag_vdb_entity(self.workspace, ids)
                logger.debug(f"Successfully deleted {deleted_count} vectors from {self.namespace}")
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                deleted_count = db_ops.delete_lightrag_vdb_relation(self.workspace, ids)
                logger.debug(f"Successfully deleted {deleted_count} vectors from {self.namespace}")
            else:
                logger.error(f"Unknown namespace for vector deletion: {self.namespace}")
        
        await asyncio.to_thread(_sync_delete)

    async def delete_entity(self, entity_name: str) -> None:
        """Delete an entity by its name from the vector storage."""
        def _sync_delete_entity():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            
            # Query entity by entity_name and delete by ID
            # Note: We need to add a method to query by entity_name in DatabaseOps
            logger.warning(f"Delete entity by name not yet fully implemented for DatabaseOps-based storage")
            
        await asyncio.to_thread(_sync_delete_entity)

    async def delete_entity_relation(self, entity_name: str) -> None:
        """Delete all relations associated with an entity."""
        def _sync_delete_entity_relation():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            
            # Query relations where source_id or target_id matches entity_name and delete by IDs
            # Note: We need to add methods to query relations by entity names in DatabaseOps
            logger.warning(f"Delete entity relations not yet fully implemented for DatabaseOps-based storage")
            
        await asyncio.to_thread(_sync_delete_entity_relation)

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get vector data by its ID"""
        def _sync_get_by_id():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace

            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                model = db_ops.query_lightrag_doc_chunks_by_id(self.workspace, id)
                if not model:
                    return None
                return {
                    "id": model.id,
                    "tokens": model.tokens,
                    "content": model.content or "",
                    "chunk_order_index": model.chunk_order_index,
                    "full_doc_id": model.full_doc_id,
                    "content_vector": model.content_vector,
                    "file_path": model.file_path,
                    "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                }
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                model = db_ops.query_lightrag_vdb_entity_by_id(self.workspace, id)
                if not model:
                    return None
                return {
                    "id": model.id,
                    "entity_name": model.entity_name,
                    "content": model.content or "",
                    "content_vector": model.content_vector,
                    "chunk_ids": model.chunk_ids,
                    "file_path": model.file_path,
                    "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                }
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                model = db_ops.query_lightrag_vdb_relation_by_id(self.workspace, id)
                if not model:
                    return None
                return {
                    "id": model.id,
                    "source_id": model.source_id,
                    "target_id": model.target_id,
                    "content": model.content or "",
                    "content_vector": model.content_vector,
                    "chunk_ids": model.chunk_ids,
                    "file_path": model.file_path,
                    "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                }
            else:
                logger.error(f"Unknown namespace for ID lookup: {self.namespace}")
                return None
        
        return await asyncio.to_thread(_sync_get_by_id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get multiple vector data by their IDs"""
        def _sync_get_by_ids():
            if not ids:
                return []

            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace

            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                models = db_ops.query_lightrag_doc_chunks_by_ids(self.workspace, ids)
                return [
                    {
                        "id": model.id,
                        "tokens": model.tokens,
                        "content": model.content or "",
                        "chunk_order_index": model.chunk_order_index,
                        "full_doc_id": model.full_doc_id,
                        "content_vector": model.content_vector,
                        "file_path": model.file_path,
                        "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                    } for model in models
                ]
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                # Note: We need to add query_lightrag_vdb_entity_by_ids method to DatabaseOps
                logger.warning(f"Batch query by IDs not yet implemented for entities in DatabaseOps")
                return []
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                # Note: We need to add query_lightrag_vdb_relation_by_ids method to DatabaseOps
                logger.warning(f"Batch query by IDs not yet implemented for relations in DatabaseOps")
                return []
            else:
                logger.error(f"Unknown namespace for IDs lookup: {self.namespace}")
                return []
        
        return await asyncio.to_thread(_sync_get_by_ids)

    async def drop(self) -> dict[str, str]:
        """Drop the storage - not implemented for safety"""
        return {"status": "error", "message": "Drop operation not supported for database-backed storage"} 