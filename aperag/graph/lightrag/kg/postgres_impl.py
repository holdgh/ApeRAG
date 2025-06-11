"""
LightRAG Module for ApeRAG

This module is based on the original LightRAG project with extensive modifications.

Original Project:
- Repository: https://github.com/HKUDS/LightRAG
- Paper: "LightRAG: Simple and Fast Retrieval-Augmented Generation" (arXiv:2410.05779)
- Authors: Zirui Guo, Lianghao Xia, Yanhua Yu, Tu Ao, Chao Huang
- License: MIT License

Modifications by ApeRAG Team:
- Removed global state management for true concurrent processing
- Added stateless interfaces for Celery/Prefect integration
- Implemented instance-level locking mechanism
- Enhanced error handling and stability
- See changelog.md for detailed modifications
"""

import asyncio
import datetime
import json
import os
from dataclasses import dataclass, field
from datetime import timezone
from typing import Any, Union, final

import asyncpg  # type: ignore
import numpy as np
from asyncpg import Pool  # type: ignore

from ..base import (
    BaseKVStorage,
    BaseVectorStorage,
    DocProcessingStatus,
    DocStatus,
    DocStatusStorage,
)
from ..namespace import NameSpace, is_namespace
from ..utils import logger


class PostgreSQLDB:
    def __init__(self, config: dict[str, Any], **kwargs: Any):
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.database = config["database"]
        self.max = int(config["max_connections"])
        self.increment = 1
        self.pool: Pool | None = None

        if self.user is None or self.password is None or self.database is None:
            raise ValueError("Missing database user, password, or database")

    async def initdb(self):
        try:
            self.pool = await asyncpg.create_pool(  # type: ignore
                user=self.user,
                password=self.password,
                database=self.database,
                host=self.host,
                port=self.port,
                min_size=1,
                max_size=self.max,
            )

            logger.info(
                f"PostgreSQL, Connected to database at {self.host}:{self.port}/{self.database}"
            )
        except Exception as e:
            logger.error(
                f"PostgreSQL, Failed to connect database at {self.host}:{self.port}/{self.database}, Got:{e}"
            )
            raise

    async def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        multirows: bool = False,
        with_age: bool = False,
        graph_name: str | None = None,
    ) -> dict[str, Any] | None | list[dict[str, Any]]:
        # start_time = time.time()
        # logger.info(f"PostgreSQL, Querying:\n{sql}")

        async with self.pool.acquire() as connection:  # type: ignore
            try:
                if params:
                    rows = await connection.fetch(sql, *params.values())
                else:
                    rows = await connection.fetch(sql)

                if multirows:
                    if rows:
                        columns = [col for col in rows[0].keys()]
                        data = [dict(zip(columns, row)) for row in rows]
                    else:
                        data = []
                else:
                    if rows:
                        columns = rows[0].keys()
                        data = dict(zip(columns, rows[0]))
                    else:
                        data = None

                # query_time = time.time() - start_time
                # logger.info(f"PostgreSQL, Query result len: {len(data)}")
                # logger.info(f"PostgreSQL, Query execution time: {query_time:.4f}s")

                return data
            except Exception as e:
                logger.error(f"PostgreSQL database, error:{e}")
                raise

    async def execute(
        self,
        sql: str,
        data: dict[str, Any] | None = None,
        upsert: bool = False,
        with_age: bool = False,
        graph_name: str | None = None,
    ):
        try:
            async with self.pool.acquire() as connection:  # type: ignore
                if data is None:
                    await connection.execute(sql)  # type: ignore
                else:
                    await connection.execute(sql, *data.values())  # type: ignore
        except (
            asyncpg.exceptions.UniqueViolationError,
            asyncpg.exceptions.DuplicateTableError,
        ) as e:
            if upsert:
                print("Key value duplicate, but upsert succeeded.")
            else:
                logger.error(f"Upsert error: {e}")
        except Exception as e:
            logger.error(f"PostgreSQL database,\nsql:{sql},\ndata:{data},\nerror:{e}")
            raise


class ClientManager:
    _instances: dict[str, Any] = {"db": None, "ref_count": 0}

    @staticmethod
    def get_config() -> dict[str, Any]:
        return {
            "host": os.environ.get("POSTGRES_HOST", "localhost"),
            "port": os.environ.get("POSTGRES_PORT", 5432),
            "user": os.environ.get("POSTGRES_USER", "postgres"),
            "password": os.environ.get("POSTGRES_PASSWORD", "password"),
            "database": os.environ.get("POSTGRES_DATABASE", "postgres"),
            "max_connections": os.environ.get("POSTGRES_MAX_CONNECTIONS", 20),
        }

    @classmethod
    async def get_client(cls, lock: asyncio.Lock = None) -> PostgreSQLDB:
        async with lock:
            if cls._instances["db"] is None:
                config = ClientManager.get_config()
                db = PostgreSQLDB(config)
                await db.initdb()
                cls._instances["db"] = db
                cls._instances["ref_count"] = 0
            cls._instances["ref_count"] += 1
            return cls._instances["db"]

    @classmethod
    async def release_client(cls, db: PostgreSQLDB, lock: asyncio.Lock = None):
        async with lock:
            if db is not None:
                if db is cls._instances["db"]:
                    cls._instances["ref_count"] -= 1
                    if cls._instances["ref_count"] == 0:
                        await db.pool.close()
                        logger.info("Closed PostgreSQL database connection pool")
                        cls._instances["db"] = None
                else:
                    await db.pool.close()


@final
@dataclass
class PGKVStorage(BaseKVStorage):
    db: PostgreSQLDB = field(default=None)

    async def initialize(self):
        if self.db is None:
            db_conn_lock = asyncio.Lock()
            self.db = await ClientManager.get_client(db_conn_lock)

    async def finalize(self):
        if self.db is not None:
            db_conn_lock = asyncio.Lock()
            await ClientManager.release_client(self.db, db_conn_lock)
            self.db = None

    ################ QUERY METHODS ################
    async def get_all(self) -> dict[str, Any]:
        """Get all data from storage

        Returns:
            Dictionary containing all stored data
        """
        table_name = namespace_to_table_name(self.namespace)
        if not table_name:
            logger.error(f"Unknown namespace for get_all: {self.namespace}")
            return {}

        sql = f"SELECT * FROM {table_name} WHERE workspace=$1"
        params = {"workspace": self.workspace}

        try:
            results = await self.db.query(sql, params, multirows=True)

            return {row["id"]: row for row in results}
        except Exception as e:
            logger.error(f"Error retrieving all data from {self.namespace}: {e}")
            return {}

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get doc_full data by id."""
        # Use storage_type property to get the correct SQL template key
        sql_key = f"get_by_id_{self.storage_type}"
        sql = SQL_TEMPLATES[sql_key]
        params = {"workspace": self.workspace, "id": id}
        response = await self.db.query(sql, params)
        return response if response else None


    # Query by id
    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get doc_chunks data by id"""
        sql_key = f"get_by_ids_{self.storage_type}"
        sql = SQL_TEMPLATES[sql_key].format(
            ids=",".join([f"'{id}'" for id in ids])
        )
        params = {"workspace": self.workspace}
        return await self.db.query(sql, params, multirows=True)


    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out duplicated content"""
        sql = SQL_TEMPLATES["filter_keys"].format(
            table_name=namespace_to_table_name(self.namespace),
            ids=",".join([f"'{id}'" for id in keys]),
        )
        params = {"workspace": self.workspace}
        try:
            res = await self.db.query(sql, params, multirows=True)
            if res:
                exist_keys = [key["id"] for key in res]
            else:
                exist_keys = []
            new_keys = set([s for s in keys if s not in exist_keys])
            return new_keys
        except Exception as e:
            logger.error(
                f"PostgreSQL database,\nsql:{sql},\nparams:{params},\nerror:{e}"
            )
            raise

    ################ INSERT METHODS ################
    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        logger.debug(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        if is_namespace(self.namespace, NameSpace.KV_STORE_FULL_DOCS):
            for k, v in data.items():
                upsert_sql = SQL_TEMPLATES["upsert_doc_full"]
                _data = {
                    "id": k,
                    "content": v["content"],
                    "workspace": self.workspace,
                }
                await self.db.execute(upsert_sql, _data)

    async def delete(self, ids: list[str]) -> None:
        """Delete specific records from storage by their IDs

        Args:
            ids (list[str]): List of document IDs to be deleted from storage

        Returns:
            None
        """
        if not ids:
            return

        table_name = namespace_to_table_name(self.namespace)
        if not table_name:
            logger.error(f"Unknown namespace for deletion: {self.namespace}")
            return

        delete_sql = f"DELETE FROM {table_name} WHERE workspace=$1 AND id = ANY($2)"

        try:
            await self.db.execute(
                delete_sql, {"workspace": self.workspace, "ids": ids}
            )
            logger.debug(
                f"Successfully deleted {len(ids)} records from {self.namespace}"
            )
        except Exception as e:
            logger.error(f"Error while deleting records from {self.namespace}: {e}")

    async def drop(self) -> dict[str, str]:
        """Drop the storage"""
        try:
            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                return {
                    "status": "error",
                    "message": f"Unknown namespace: {self.namespace}",
                }

            drop_sql = SQL_TEMPLATES["drop_specifiy_table_workspace"].format(
                table_name=table_name
            )
            await self.db.execute(drop_sql, {"workspace": self.workspace})
            return {"status": "success", "message": "data dropped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


@final
@dataclass
class PGVectorStorage(BaseVectorStorage):
    db: PostgreSQLDB | None = field(default=None)

    async def initialize(self):
        if self.db is None:
            db_conn_lock = asyncio.Lock()
            self.db = await ClientManager.get_client(db_conn_lock)

    async def finalize(self):
        if self.db is not None:
            db_conn_lock = asyncio.Lock()
            await ClientManager.release_client(self.db, db_conn_lock)
            self.db = None

    def _upsert_chunks(
        self, item: dict[str, Any], current_time: datetime.datetime
    ) -> tuple[str, dict[str, Any]]:
        try:
            upsert_sql = SQL_TEMPLATES["upsert_chunk"]
            data: dict[str, Any] = {
                "workspace": self.workspace,
                "id": item["__id__"],
                "tokens": item["tokens"],
                "chunk_order_index": item["chunk_order_index"],
                "full_doc_id": item["full_doc_id"],
                "content": item["content"],
                "content_vector": json.dumps(item["__vector__"].tolist()),
                "file_path": item["file_path"],
                "create_time": current_time,
                "update_time": current_time,
            }
        except Exception as e:
            logger.error(f"Error to prepare upsert,\nsql: {e}\nitem: {item}")
            raise

        return upsert_sql, data

    def _upsert_entities(
        self, item: dict[str, Any], current_time: datetime.datetime
    ) -> tuple[str, dict[str, Any]]:
        upsert_sql = SQL_TEMPLATES["upsert_entity"]
        source_id = item["source_id"]
        if isinstance(source_id, str) and "<SEP>" in source_id:
            chunk_ids = source_id.split("<SEP>")
        else:
            chunk_ids = [source_id]

        data: dict[str, Any] = {
            "workspace": self.workspace,
            "id": item["__id__"],
            "entity_name": item["entity_name"],
            "content": item["content"],
            "content_vector": json.dumps(item["__vector__"].tolist()),
            "chunk_ids": chunk_ids,
            "file_path": item.get("file_path", None),
            "create_time": current_time,
            "update_time": current_time,
        }
        return upsert_sql, data

    def _upsert_relationships(
        self, item: dict[str, Any], current_time: datetime.datetime
    ) -> tuple[str, dict[str, Any]]:
        upsert_sql = SQL_TEMPLATES["upsert_relationship"]
        source_id = item["source_id"]
        if isinstance(source_id, str) and "<SEP>" in source_id:
            chunk_ids = source_id.split("<SEP>")
        else:
            chunk_ids = [source_id]

        data: dict[str, Any] = {
            "workspace": self.workspace,
            "id": item["__id__"],
            "source_id": item["src_id"],
            "target_id": item["tgt_id"],
            "content": item["content"],
            "content_vector": json.dumps(item["__vector__"].tolist()),
            "chunk_ids": chunk_ids,
            "file_path": item.get("file_path", None),
            "create_time": current_time,
            "update_time": current_time,
        }
        return upsert_sql, data

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
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
        for item in list_data:
            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                upsert_sql, data = self._upsert_chunks(item, current_time)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                upsert_sql, data = self._upsert_entities(item, current_time)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                upsert_sql, data = self._upsert_relationships(item, current_time)
            else:
                raise ValueError(f"{self.namespace} is not supported")

            await self.db.execute(upsert_sql, data)

    #################### query method ###############
    async def query(
        self, query: str, top_k: int, ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        embeddings = await self.embedding_func(
            [query]
        )  # higher priority for query
        embedding = embeddings[0]
        embedding_string = ",".join(map(str, embedding))
        # Use parameterized document IDs (None means search across all documents)
        sql = SQL_TEMPLATES[self.storage_type].format(embedding_string=embedding_string)
        params = {
            "workspace": self.workspace,
            "doc_ids": ids,
            "better_than_threshold": self.cosine_better_than_threshold,
            "top_k": top_k,
        }
        results = await self.db.query(sql, params=params, multirows=True)
        return results

    async def delete(self, ids: list[str]) -> None:
        """Delete vectors with specified IDs from the storage.

        Args:
            ids: List of vector IDs to be deleted
        """
        if not ids:
            return

        table_name = namespace_to_table_name(self.namespace)
        if not table_name:
            logger.error(f"Unknown namespace for vector deletion: {self.namespace}")
            return

        delete_sql = f"DELETE FROM {table_name} WHERE workspace=$1 AND id = ANY($2)"

        try:
            await self.db.execute(
                delete_sql, {"workspace": self.workspace, "ids": ids}
            )
            logger.debug(
                f"Successfully deleted {len(ids)} vectors from {self.namespace}"
            )
        except Exception as e:
            logger.error(f"Error while deleting vectors from {self.namespace}: {e}")

    async def delete_entity(self, entity_name: str) -> None:
        """Delete an entity by its name from the vector storage.

        Args:
            entity_name: The name of the entity to delete
        """
        try:
            # Construct SQL to delete the entity
            delete_sql = """DELETE FROM LIGHTRAG_VDB_ENTITY
                            WHERE workspace=$1 AND entity_name=$2"""

            await self.db.execute(
                delete_sql, {"workspace": self.workspace, "entity_name": entity_name}
            )
            logger.debug(f"Successfully deleted entity {entity_name}")
        except Exception as e:
            logger.error(f"Error deleting entity {entity_name}: {e}")

    async def delete_entity_relation(self, entity_name: str) -> None:
        """Delete all relations associated with an entity.

        Args:
            entity_name: The name of the entity whose relations should be deleted
        """
        try:
            # Delete relations where the entity is either the source or target
            delete_sql = """DELETE FROM LIGHTRAG_VDB_RELATION
                            WHERE workspace=$1 AND (source_id=$2 OR target_id=$2)"""

            await self.db.execute(
                delete_sql, {"workspace": self.workspace, "entity_name": entity_name}
            )
            logger.debug(f"Successfully deleted relations for entity {entity_name}")
        except Exception as e:
            logger.error(f"Error deleting relations for entity {entity_name}: {e}")

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get vector data by its ID

        Args:
            id: The unique identifier of the vector

        Returns:
            The vector data if found, or None if not found
        """
        table_name = namespace_to_table_name(self.namespace)
        if not table_name:
            logger.error(f"Unknown namespace for ID lookup: {self.namespace}")
            return None

        query = f"SELECT *, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM {table_name} WHERE workspace=$1 AND id=$2"
        params = {"workspace": self.workspace, "id": id}

        try:
            result = await self.db.query(query, params)
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"Error retrieving vector data for ID {id}: {e}")
            return None

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get multiple vector data by their IDs

        Args:
            ids: List of unique identifiers

        Returns:
            List of vector data objects that were found
        """
        if not ids:
            return []

        table_name = namespace_to_table_name(self.namespace)
        if not table_name:
            logger.error(f"Unknown namespace for IDs lookup: {self.namespace}")
            return []

        ids_str = ",".join([f"'{id}'" for id in ids])
        query = f"SELECT *, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM {table_name} WHERE workspace=$1 AND id IN ({ids_str})"
        params = {"workspace": self.workspace}

        try:
            results = await self.db.query(query, params, multirows=True)
            return [dict(record) for record in results]
        except Exception as e:
            logger.error(f"Error retrieving vector data for IDs {ids}: {e}")
            return []

    async def drop(self) -> dict[str, str]:
        """Drop the storage"""
        try:
            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                return {
                    "status": "error",
                    "message": f"Unknown namespace: {self.namespace}",
                }

            drop_sql = SQL_TEMPLATES["drop_specifiy_table_workspace"].format(
                table_name=table_name
            )
            await self.db.execute(drop_sql, {"workspace": self.workspace})
            return {"status": "success", "message": "data dropped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


@final
@dataclass
class PGDocStatusStorage(DocStatusStorage):
    db: PostgreSQLDB = field(default=None)

    async def initialize(self):
        if self.db is None:
            db_conn_lock = asyncio.Lock()
            self.db = await ClientManager.get_client(db_conn_lock)

    async def finalize(self):
        if self.db is not None:
            db_conn_lock = asyncio.Lock()
            await ClientManager.release_client(self.db, db_conn_lock)
            self.db = None

    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Filter out duplicated content"""
        sql = SQL_TEMPLATES["filter_keys"].format(
            table_name=namespace_to_table_name(self.namespace),
            ids=",".join([f"'{id}'" for id in keys]),
        )
        params = {"workspace": self.workspace}
        try:
            res = await self.db.query(sql, params, multirows=True)
            if res:
                exist_keys = [key["id"] for key in res]
            else:
                exist_keys = []
            new_keys = set([s for s in keys if s not in exist_keys])
            print(f"keys: {keys}")
            print(f"new_keys: {new_keys}")
            return new_keys
        except Exception as e:
            logger.error(
                f"PostgreSQL database,\nsql:{sql},\nparams:{params},\nerror:{e}"
            )
            raise

    async def get_by_id(self, id: str) -> Union[dict[str, Any], None]:
        sql = "select * from LIGHTRAG_DOC_STATUS where workspace=$1 and id=$2"
        params = {"workspace": self.workspace, "id": id}
        result = await self.db.query(sql, params, True)
        if result is None or result == []:
            return None
        else:
            return dict(
                content=result[0]["content"],
                content_length=result[0]["content_length"],
                content_summary=result[0]["content_summary"],
                status=result[0]["status"],
                chunks_count=result[0]["chunks_count"],
                created_at=result[0]["created_at"],
                updated_at=result[0]["updated_at"],
                file_path=result[0]["file_path"],
            )

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get doc_chunks data by multiple IDs."""
        if not ids:
            return []

        sql = "SELECT * FROM LIGHTRAG_DOC_STATUS WHERE workspace=$1 AND id = ANY($2)"
        params = {"workspace": self.workspace, "ids": ids}

        results = await self.db.query(sql, params, True)

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

    async def get_status_counts(self) -> dict[str, int]:
        """Get counts of documents in each status"""
        sql = """SELECT status as "status", COUNT(1) as "count"
                   FROM LIGHTRAG_DOC_STATUS
                  where workspace=$1 GROUP BY STATUS
                 """
        result = await self.db.query(sql, {"workspace": self.workspace}, True)
        counts = {}
        for doc in result:
            counts[doc["status"]] = doc["count"]
        return counts

    async def get_docs_by_status(
        self, status: DocStatus
    ) -> dict[str, DocProcessingStatus]:
        """all documents with a specific status"""
        sql = "select * from LIGHTRAG_DOC_STATUS where workspace=$1 and status=$2"
        params = {"workspace": self.workspace, "status": status.value}
        result = await self.db.query(sql, params, True)
        docs_by_status = {
            element["id"]: DocProcessingStatus(
                content=element["content"],
                content_summary=element["content_summary"],
                content_length=element["content_length"],
                status=element["status"],
                created_at=element["created_at"],
                updated_at=element["updated_at"],
                chunks_count=element["chunks_count"],
                file_path=element["file_path"],
            )
            for element in result
        }
        return docs_by_status

    async def delete(self, ids: list[str]) -> None:
        """Delete specific records from storage by their IDs

        Args:
            ids (list[str]): List of document IDs to be deleted from storage

        Returns:
            None
        """
        if not ids:
            return

        table_name = namespace_to_table_name(self.namespace)
        if not table_name:
            logger.error(f"Unknown namespace for deletion: {self.namespace}")
            return

        delete_sql = f"DELETE FROM {table_name} WHERE workspace=$1 AND id = ANY($2)"

        try:
            await self.db.execute(
                delete_sql, {"workspace": self.workspace, "ids": ids}
            )
            logger.debug(
                f"Successfully deleted {len(ids)} records from {self.namespace}"
            )
        except Exception as e:
            logger.error(f"Error while deleting records from {self.namespace}: {e}")

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """Update or insert document status

        Args:
            data: dictionary of document IDs and their status data
        """
        logger.debug(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        def parse_datetime(dt_str):
            if dt_str is None:
                return None
            if isinstance(dt_str, (datetime.date, datetime.datetime)):
                # If it's a datetime object without timezone info, remove timezone info
                if isinstance(dt_str, datetime.datetime):
                    # Remove timezone info, return naive datetime object
                    return dt_str.replace(tzinfo=None)
                return dt_str
            try:
                # Process ISO format string with timezone
                dt = datetime.datetime.fromisoformat(dt_str)
                # Remove timezone info, return naive datetime object
                return dt.replace(tzinfo=None)
            except (ValueError, TypeError):
                logger.warning(f"Unable to parse datetime string: {dt_str}")
                return None

        # Modified SQL to include created_at and updated_at in both INSERT and UPDATE operations
        # Both fields are updated from the input data in both INSERT and UPDATE cases
        sql = """insert into LIGHTRAG_DOC_STATUS(workspace,id,content,content_summary,content_length,chunks_count,status,file_path,created_at,updated_at)
                 values($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                  on conflict(id,workspace) do update set
                  content = EXCLUDED.content,
                  content_summary = EXCLUDED.content_summary,
                  content_length = EXCLUDED.content_length,
                  chunks_count = EXCLUDED.chunks_count,
                  status = EXCLUDED.status,
                  file_path = EXCLUDED.file_path,
                  created_at = EXCLUDED.created_at,
                  updated_at = EXCLUDED.updated_at"""
        for k, v in data.items():
            # Remove timezone information, store utc time in db
            created_at = parse_datetime(v.get("created_at"))
            updated_at = parse_datetime(v.get("updated_at"))

            # chunks_count is optional
            await self.db.execute(
                sql,
                {
                    "workspace": self.workspace,
                    "id": k,
                    "content": v["content"],
                    "content_summary": v["content_summary"],
                    "content_length": v["content_length"],
                    "chunks_count": v["chunks_count"] if "chunks_count" in v else -1,
                    "status": v["status"],
                    "file_path": v["file_path"],
                    "created_at": created_at,  # Use the converted datetime object
                    "updated_at": updated_at,  # Use the converted datetime object
                },
            )

    async def drop(self) -> dict[str, str]:
        """Drop the storage"""
        try:
            table_name = namespace_to_table_name(self.namespace)
            if not table_name:
                return {
                    "status": "error",
                    "message": f"Unknown namespace: {self.namespace}",
                }

            drop_sql = SQL_TEMPLATES["drop_specifiy_table_workspace"].format(
                table_name=table_name
            )
            await self.db.execute(drop_sql, {"workspace": self.workspace})
            return {"status": "success", "message": "data dropped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


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
    # SQL for KVStorage
    "get_by_id_full_docs": """SELECT id, COALESCE(content, '') as content
                                FROM LIGHTRAG_DOC_FULL WHERE workspace=$1 AND id=$2
                            """,
    "get_by_id_text_chunks": """SELECT id, tokens, COALESCE(content, '') as content,
                                chunk_order_index, full_doc_id, file_path
                                FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=$1 AND id=$2
                            """,
    "get_by_ids_full_docs": """SELECT id, COALESCE(content, '') as content
                                 FROM LIGHTRAG_DOC_FULL WHERE workspace=$1 AND id IN ({ids})
                            """,
    "get_by_ids_text_chunks": """SELECT id, tokens, COALESCE(content, '') as content,
                                  chunk_order_index, full_doc_id, file_path
                                   FROM LIGHTRAG_DOC_CHUNKS WHERE workspace=$1 AND id IN ({ids})
                                """,
    "filter_keys": "SELECT id FROM {table_name} WHERE workspace=$1 AND id IN ({ids})",
    "upsert_doc_full": """INSERT INTO LIGHTRAG_DOC_FULL (id, content, workspace)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (workspace,id) DO UPDATE
                           SET content = $2, update_time = CURRENT_TIMESTAMP
                       """,
    "upsert_chunk": """INSERT INTO LIGHTRAG_DOC_CHUNKS (workspace, id, tokens,
                      chunk_order_index, full_doc_id, content, content_vector, file_path,
                      create_time, update_time)
                      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
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
                      VALUES ($1, $2, $3, $4, $5, $6::varchar[], $7, $8, $9)
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
                      VALUES ($1, $2, $3, $4, $5, $6, $7::varchar[], $8, $9, $10)
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
        WHERE $2::varchar[] IS NULL OR full_doc_id = ANY($2::varchar[])
    )
    SELECT source_id as src_id, target_id as tgt_id, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at
    FROM (
        SELECT r.id, r.source_id, r.target_id, r.create_time, 1 - (r.content_vector <=> '[{embedding_string}]'::vector) as distance
        FROM LIGHTRAG_VDB_RELATION r
        JOIN relevant_chunks c ON c.chunk_id = ANY(r.chunk_ids)
        WHERE r.workspace=$1
    ) filtered
    WHERE distance>$3
    ORDER BY distance DESC
    LIMIT $4
    """,
    "entities": """
        WITH relevant_chunks AS (
            SELECT id as chunk_id
            FROM LIGHTRAG_DOC_CHUNKS
            WHERE $2::varchar[] IS NULL OR full_doc_id = ANY($2::varchar[])
        )
        SELECT entity_name, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM
            (
                SELECT e.id, e.entity_name, e.create_time, 1 - (e.content_vector <=> '[{embedding_string}]'::vector) as distance
                FROM LIGHTRAG_VDB_ENTITY e
                JOIN relevant_chunks c ON c.chunk_id = ANY(e.chunk_ids)
                WHERE e.workspace=$1
            ) as chunk_distances
            WHERE distance>$3
            ORDER BY distance DESC
            LIMIT $4
    """,
    "chunks": """
        WITH relevant_chunks AS (
            SELECT id as chunk_id
            FROM LIGHTRAG_DOC_CHUNKS
            WHERE $2::varchar[] IS NULL OR full_doc_id = ANY($2::varchar[])
        )
        SELECT id, content, file_path, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM
            (
                SELECT id, content, file_path, create_time, 1 - (content_vector <=> '[{embedding_string}]'::vector) as distance
                FROM LIGHTRAG_DOC_CHUNKS
                WHERE workspace=$1
                AND id IN (SELECT chunk_id FROM relevant_chunks)
            ) as chunk_distances
            WHERE distance>$3
            ORDER BY distance DESC
            LIMIT $4
    """,
    # DROP tables
    "drop_specifiy_table_workspace": """
        DELETE FROM {table_name} WHERE workspace=$1
       """,
}
