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
from dataclasses import dataclass
from datetime import timezone
from typing import Any, final

import numpy as np

from ..base import (
    BaseVectorStorage,
)
from ..utils import logger


@final
@dataclass
class PGOpsSyncVectorStorage(BaseVectorStorage):
    """PostgreSQL Vector Storage using DatabaseOps with sync interface."""

    async def initialize(self):
        """Initialize storage."""
        logger.debug(f"PGOpsSyncVectorStorage initialized for workspace '{self.workspace}'")

    async def finalize(self):
        """Clean up resources."""
        logger.debug(f"PGOpsSyncVectorStorage finalized for workspace '{self.workspace}'")

    async def get_all(self) -> dict[str, Any]:
        """Get all data from vector storage"""

        def _sync_get_all():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace

            # Determine which table to query based on namespace
            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                models = db_ops.query_lightrag_doc_chunks_all(self.workspace)
                return {
                    chunk_id: {
                        "id": chunk_id,
                        "tokens": model.tokens,
                        "content": model.content or "",
                        "chunk_order_index": model.chunk_order_index,
                        "full_doc_id": model.full_doc_id,
                        "content_vector": model.content_vector,
                        "file_path": model.file_path,
                        "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                    }
                    for chunk_id, model in models.items()
                }
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                models = db_ops.query_lightrag_vdb_entity_all(self.workspace)
                return {
                    entity_id: {
                        "id": entity_id,
                        "entity_name": model.entity_name,
                        "content": model.content or "",
                        "content_vector": model.content_vector,
                        "chunk_ids": model.chunk_ids or [],
                        "file_path": model.file_path,
                        "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                    }
                    for entity_id, model in models.items()
                }
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                models = db_ops.query_lightrag_vdb_relation_all(self.workspace)
                return {
                    relation_id: {
                        "id": relation_id,
                        "source_id": model.source_id,
                        "target_id": model.target_id,
                        "content": model.content or "",
                        "content_vector": model.content_vector,
                        "chunk_ids": model.chunk_ids or [],
                        "file_path": model.file_path,
                        "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                        # Add additional fields that might be expected
                        "src_id": model.source_id,
                        "tgt_id": model.target_id,
                    }
                    for relation_id, model in models.items()
                }
            else:
                logger.error(f"Unknown namespace for get_all: {self.namespace}")
                return {}

        return await asyncio.to_thread(_sync_get_all)

    def _prepare_vector_data(self, item: dict[str, Any], current_time: datetime.datetime) -> dict[str, Any]:  # 基于分段内容和embedding结果构造vector_data
        """Prepare vector data based on namespace."""
        from aperag.graph.lightrag.namespace import NameSpace, is_namespace
        # chunk对应的namespace属性为NameSpace.VECTOR_STORE_CHUNKS【chunks】，见aperag.graph.lightrag.lightrag.LightRAG.__post_init__中对于chunks_vdb的初始化
        if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
            return {
                "tokens": item["tokens"],  # 当前分段内容的长度
                "chunk_order_index": item["chunk_order_index"],  # 当前分段内容在原始文档解析结果markdown文本中的索引顺序
                "full_doc_id": item["full_doc_id"],
                "content": item["content"],  # 分段内容
                "content_vector": item["__vector__"].tolist()
                if hasattr(item["__vector__"], "tolist")
                else item["__vector__"],  # embedding向量
                "file_path": item.get("file_path"),  # 原始文件路径
            }
        elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
            source_id = item["source_id"]
            chunk_ids = source_id.split("<SEP>") if isinstance(source_id, str) and "<SEP>" in source_id else [source_id]
            return {
                "entity_name": item["entity_name"],
                "content": item["content"],
                "content_vector": item["__vector__"].tolist()
                if hasattr(item["__vector__"], "tolist")
                else item["__vector__"],
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
                "content_vector": item["__vector__"].tolist()
                if hasattr(item["__vector__"], "tolist")
                else item["__vector__"],
                "chunk_ids": chunk_ids,
                "file_path": item.get("file_path"),
            }
        else:
            raise ValueError(f"{self.namespace} is not supported")

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:  # 将分段数据【分批embedding处理后】保存至数据库【被多处调用，有：关系relation、实体entity、分段chunk】
        """
        data形如：
        {"分段1_id": {
                    "tokens": min(max_token_size, len(tokens) - start),  # 分段1的长度
                    "content": chunk_content.strip(),  # 分段1的文本内容
                    "chunk_order_index": index,  # 分段1的索引【相对整个文档的content而言】
                    "full_doc_id": doc_id,  # 原始文档id
                    "file_path": file_path,  # 原始文档路径
                }
        }
        """
        """Insert or update vector data"""
        # -- 校验分段数据非空
        logger.debug(f"Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        # Get current time with UTC timezone
        current_time = datetime.datetime.now(timezone.utc)
        # -- 构造分段数据记录
        list_data = [
            {
                "__id__": k,
                **{k1: v1 for k1, v1 in v.items()},
            }
            for k, v in data.items()
        ]  # 构造分段数据记录列表
        # -- 分批对分段文本进行embedding处理
        # Compute embeddings first (async)
        contents = [v["content"] for v in data.values()]  # 获取当前所有分段文本
        batches = [contents[i : i + self._max_batch_size] for i in range(0, len(contents), self._max_batch_size)]  # 分批【默认每批32个分段文本】
        # 单一批次的分段文本对应一个embedding结果，而一个embedding结果是对应批次尺寸个embedding向量【合理，一个分段文本对应一个embedding向量】
        embedding_tasks = [self.embedding_func(batch) for batch in batches]  # 分批创建embedding任务
        embeddings_list = await asyncio.gather(*embedding_tasks)  # 异步执行，获取各批次embedding结果
        # np.concatenate() 是 numpy 库的函数，用于将多个数组沿着指定轴（默认是第 0 轴，即行方向）连接起来，形成一个更大的数组。
        embeddings = np.concatenate(embeddings_list)  # 将各批次的embedding结果列表合并为embedding“矩阵”
        # -- 为上述分段记录列表中的每一个分段记录添加embedding向量字段
        for i, d in enumerate(list_data):
            d["__vector__"] = embeddings[i]  # 此处表明：上述单批次的embedding结果也是一个“【批次大小】*【embedding向量维度】的矩阵”

        def _sync_upsert_with_vectors():  # 批量保存或更新分段数据
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace
            # -- 对分段数据进一步封装处理【对应数据表记录的字典】
            # Prepare data for each item
            vector_data = {}
            for item in list_data:
                item_id = item["__id__"]
                prepared_data = self._prepare_vector_data(item, current_time)
                vector_data[item_id] = prepared_data

            # Use appropriate DatabaseOps method based on namespace
            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):  # 保存或更新分段数据【基于(知识库id,分段id)是否已存在】
                db_ops.upsert_lightrag_doc_chunks(self.workspace, vector_data)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):  # 保存或更新实体数据
                db_ops.upsert_lightrag_vdb_entity(self.workspace, vector_data)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):  # 保存或更新关系数据【边】
                db_ops.upsert_lightrag_vdb_relation(self.workspace, vector_data)
            else:
                raise ValueError(f"{self.namespace} is not supported")

        await asyncio.to_thread(_sync_upsert_with_vectors)  # 批量保存或更新分段数据

    async def query(self, query: str, top_k: int, ids: list[str] | None = None) -> list[dict[str, Any]]:  # 对query【用户问题、高/低级别关键词】，基于embedding相似度机制检索数据
        """Query vectors by similarity"""
        # Compute embedding for query
        embeddings = await self.embedding_func([query])  # 对query【用户问题、高/低级别关键词】进行embedding
        embedding = embeddings[0]

        def _sync_query():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops
            from aperag.graph.lightrag.namespace import NameSpace, is_namespace

            # Convert embedding to list if it's numpy array
            if hasattr(embedding, "tolist"):
                embedding_list = embedding.tolist()
            else:
                embedding_list = list(embedding)

            # Use appropriate similarity search method based on namespace
            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):  # 分段内容
                results = db_ops.query_lightrag_doc_chunks_similarity(
                    self.workspace, embedding_list, top_k, ids, self.cosine_better_than_threshold
                )
                # Convert results to expected format for chunks
                formatted_results = []
                for result in results:
                    if hasattr(result, "_asdict"):
                        # Handle NamedTuple or Row objects
                        row_dict = result._asdict()
                    elif isinstance(result, dict):
                        row_dict = result
                    else:
                        # Convert Row object to dict manually
                        row_dict = {key: getattr(result, key) for key in result.keys()}

                    formatted_results.append(
                        {
                            "id": row_dict.get("id"),
                            "content": row_dict.get("content", ""),
                            "file_path": row_dict.get("file_path"),
                            "created_at": row_dict.get("created_at"),
                        }
                    )
                return formatted_results

            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):  # 实体
                results = db_ops.query_lightrag_vdb_entity_similarity(
                    self.workspace, embedding_list, top_k, ids, self.cosine_better_than_threshold
                )
                # Convert results to expected format for entities
                formatted_results = []
                for result in results:
                    if hasattr(result, "_asdict"):
                        # Handle NamedTuple or Row objects
                        row_dict = result._asdict()
                    elif isinstance(result, dict):
                        row_dict = result
                    else:
                        # Convert Row object to dict manually
                        row_dict = {key: getattr(result, key) for key in result.keys()}

                    formatted_results.append(
                        {"entity_name": row_dict.get("entity_name"), "created_at": row_dict.get("created_at")}
                    )
                return formatted_results

            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):  # 关系
                results = db_ops.query_lightrag_vdb_relation_similarity(
                    self.workspace, embedding_list, top_k, ids, self.cosine_better_than_threshold
                )
                # Convert results to expected format for relationships
                formatted_results = []
                for result in results:
                    if hasattr(result, "_asdict"):
                        # Handle NamedTuple or Row objects
                        row_dict = result._asdict()
                    elif isinstance(result, dict):
                        row_dict = result
                    else:
                        # Convert Row object to dict manually
                        row_dict = {key: getattr(result, key) for key in result.keys()}

                    formatted_results.append(
                        {
                            "src_id": row_dict.get("src_id"),
                            "tgt_id": row_dict.get("tgt_id"),
                            "created_at": row_dict.get("created_at"),
                        }
                    )
                return formatted_results

            else:
                logger.error(f"Unknown namespace for vector similarity query: {self.namespace}")
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

            try:
                # Use the new delete by name method
                deleted_count = db_ops.delete_lightrag_vdb_entity_by_name(self.workspace, entity_name)
                if deleted_count > 0:
                    logger.debug(f"Successfully deleted entity {entity_name}")
                else:
                    logger.debug(f"Entity {entity_name} not found")
            except Exception as e:
                logger.error(f"Error deleting entity {entity_name}: {e}")

        await asyncio.to_thread(_sync_delete_entity)

    async def delete_entity_relation(self, entity_name: str) -> None:
        """Delete all relations associated with an entity."""

        def _sync_delete_entity_relation():
            # Import here to avoid circular imports
            from aperag.db.ops import db_ops

            try:
                # Use the new delete relations by entity method
                deleted_count = db_ops.delete_lightrag_vdb_relation_by_entity(self.workspace, entity_name)
                logger.debug(f"Successfully deleted {deleted_count} relations for entity {entity_name}")
            except Exception as e:
                logger.error(f"Error deleting relations for entity {entity_name}: {e}")

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
                    }
                    for model in models
                ]
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                # Use the new batch query method for entities
                models = db_ops.query_lightrag_vdb_entity_by_ids(self.workspace, ids)
                return [
                    {
                        "id": model.id,
                        "entity_name": model.entity_name,
                        "content": model.content or "",
                        "content_vector": model.content_vector,
                        "chunk_ids": model.chunk_ids,
                        "file_path": model.file_path,
                        "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                    }
                    for model in models
                ]
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                # Use the new batch query method for relations
                models = db_ops.query_lightrag_vdb_relation_by_ids(self.workspace, ids)
                return [
                    {
                        "id": model.id,
                        "source_id": model.source_id,
                        "target_id": model.target_id,
                        "content": model.content or "",
                        "content_vector": model.content_vector,
                        "chunk_ids": model.chunk_ids,
                        "file_path": model.file_path,
                        "created_at": int(model.create_time.timestamp()) if model.create_time else None,
                    }
                    for model in models
                ]
            else:
                logger.error(f"Unknown namespace for IDs lookup: {self.namespace}")
                return []

        return await asyncio.to_thread(_sync_get_by_ids)

    async def drop(self) -> dict[str, str]:
        """Drop the storage - not implemented for safety"""
        return {"status": "error", "message": "Drop operation not supported for database-backed storage"}
