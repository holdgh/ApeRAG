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
from typing import List, Optional, Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.db import models as db_models
from aperag.db.ops import AsyncDatabaseOps, async_db_ops
from aperag.exceptions import ValidationException
from aperag.flow.base.models import Edge, FlowInstance, NodeInstance
from aperag.flow.engine import FlowEngine
from aperag.schema import view_models
from aperag.schema.utils import dumpCollectionConfig, parseCollectionConfig
from aperag.schema.view_models import (
    Collection,
    SearchResult,
    SearchResultItem,
    SearchResultList,
)
from aperag.service.collection_summary_service import collection_summary_service
from aperag.service.marketplace_collection_service import marketplace_collection_service
from aperag.service.marketplace_service import marketplace_service
from aperag.utils.constant import QuotaType
from aperag.views.utils import validate_source_connect_config
from config.celery_tasks import collection_delete_task, collection_init_task

logger = logging.getLogger(__name__)


class CollectionService:
    """Collection service that handles business logic for collections"""

    def __init__(self, session: AsyncSession = None):
        # Use global db_ops instance by default, or create custom one with provided session
        if session is None:
            self.db_ops = async_db_ops  # Use global instance
        else:
            self.db_ops = AsyncDatabaseOps(session)  # Create custom instance for transaction control

    async def build_collection_response(self, instance: db_models.Collection) -> view_models.Collection:
        """Build Collection response object for API return."""
        return Collection(
            id=instance.id,
            title=instance.title,
            description=instance.description,
            type=instance.type,
            status=getattr(instance, "status", None),
            config=parseCollectionConfig(instance.config),
            created=instance.gmt_created.isoformat(),
            updated=instance.gmt_updated.isoformat(),
        )

    async def create_collection(self, user: str, collection: view_models.CollectionCreate) -> view_models.Collection:
        collection_config = collection.config
        if collection.type != db_models.CollectionType.DOCUMENT:
            raise ValidationException("collection type is not supported")

        is_validate, error_msg = validate_source_connect_config(collection_config)
        if not is_validate:
            raise ValidationException(error_msg)

        # Create collection and consume quota in a single transaction
        async def _create_collection_with_quota(session):
            from aperag.service.quota_service import quota_service

            # Check and consume quota within the transaction
            await quota_service.check_and_consume_quota(user, "max_collection_count", 1, session)

            # Create collection within the same transaction
            config_str = dumpCollectionConfig(collection_config) if collection.config is not None else None

            from aperag.db.models import Collection, CollectionStatus
            from aperag.utils.utils import utc_now

            instance = Collection(
                user=user,
                title=collection.title,
                description=collection.description,
                type=collection.type,
                status=CollectionStatus.ACTIVE,
                config=config_str,
                gmt_created=utc_now(),
                gmt_updated=utc_now(),
            )
            session.add(instance)
            await session.flush()
            await session.refresh(instance)

            return instance

        instance = await self.db_ops.execute_with_transaction(_create_collection_with_quota)

        if collection.config.enable_summary:
            await collection_summary_service.trigger_collection_summary_generation(instance)

        # Initialize collection based on type
        document_user_quota = await self.db_ops.query_user_quota(user, QuotaType.MAX_DOCUMENT_COUNT)
        collection_init_task.delay(instance.id, document_user_quota)

        return await self.build_collection_response(instance)

    async def list_collections_view(
        self, user_id: str, include_subscribed: bool = True, page: int = 1, page_size: int = 20
    ) -> view_models.CollectionViewList:
        """
        Get user's collection list (lightweight view)

        Args:
            user_id: User ID
            include_subscribed: Whether to include subscribed collections, default True
            page: Page number
            page_size: Page size
        """
        items = []

        # 1. Get user's owned collections with marketplace info
        owned_collections_data = await self.db_ops.query_collections_with_marketplace_info(user_id)

        for row in owned_collections_data:
            is_published = row.marketplace_status == "PUBLISHED"
            items.append(
                view_models.CollectionView(
                    id=row.id,
                    title=row.title,
                    description=row.description,
                    type=row.type,
                    status=row.status,
                    created=row.gmt_created,
                    updated=row.gmt_updated,
                    is_published=is_published,
                    published_at=row.published_at if is_published else None,
                    owner_user_id=row.user,
                    owner_username=row.owner_username,
                    subscription_id=None,  # Own collection, subscription_id is None
                    subscribed_at=None,
                )
            )

        # 2. Get subscribed collections if needed (optimized - no N+1 queries)
        if include_subscribed:
            try:
                # Get subscribed collections data with all needed fields in one query
                subscribed_collections_data, _ = await self.db_ops.list_user_subscribed_collections(
                    user_id,
                    page=1,
                    page_size=1000,  # Get all subscriptions for now
                )

                for data in subscribed_collections_data:
                    is_published = data["marketplace_status"] == "PUBLISHED"
                    items.append(
                        view_models.CollectionView(
                            id=data["id"],
                            title=data["title"],
                            description=data["description"],
                            type=data["type"],
                            status=data["status"],
                            created=data["gmt_created"],
                            updated=data["gmt_updated"],
                            is_published=is_published,
                            published_at=data["published_at"] if is_published else None,
                            owner_user_id=data["owner_user_id"],
                            owner_username=data["owner_username"],
                            subscription_id=data["subscription_id"],
                            subscribed_at=data["gmt_subscribed"],
                        )
                    )
            except Exception as e:
                # If getting subscriptions fails, log and continue with owned collections
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get subscribed collections for user {user_id}: {e}")

        # 3. Sort by update time
        items.sort(key=lambda x: x.updated or x.created, reverse=True)

        # 4. Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = items[start_idx:end_idx]

        return view_models.CollectionViewList(
            items=paginated_items, pageResult=view_models.PageResult(total=len(items), page=page, page_size=page_size)
        )

    async def get_collection(self, user: str, collection_id: str) -> view_models.Collection:
        from aperag.exceptions import CollectionNotFoundException

        if not user:
            await marketplace_service.validate_marketplace_collection(collection_id)
            collection = await self.db_ops.query_collection_by_id(collection_id)
        else:
            collection = await self.db_ops.query_collection(user, collection_id)

        if collection is None:
            raise CollectionNotFoundException(collection_id)
        return await self.build_collection_response(collection)

    async def update_collection(
        self, user: str, collection_id: str, collection: view_models.CollectionUpdate
    ) -> view_models.Collection:
        from aperag.exceptions import CollectionNotFoundException

        # First check if collection exists
        instance = await self.db_ops.query_collection(user, collection_id)
        if instance is None:
            raise CollectionNotFoundException(collection_id)

        # Direct call to repository method, which handles its own transaction
        config_str = dumpCollectionConfig(collection.config)

        updated_instance = await self.db_ops.update_collection_by_id(
            user=user,
            collection_id=collection_id,
            title=collection.title,
            description=collection.description,
            config=config_str,
        )

        await collection_summary_service.trigger_collection_summary_generation(updated_instance)

        if not updated_instance:
            raise CollectionNotFoundException(collection_id)

        return await self.build_collection_response(updated_instance)

    async def delete_collection(self, user: str, collection_id: str) -> Optional[view_models.Collection]:
        """Delete collection by ID (idempotent operation)

        Returns the deleted collection or None if already deleted/not found
        """
        # Check if collection exists - if not, silently succeed (idempotent)
        collection = await self.db_ops.query_collection(user, collection_id)
        if collection is None:
            return None

        # Delete collection and release quota in a single transaction
        async def _delete_collection_with_quota(session):
            from sqlalchemy import select

            from aperag.db.models import CollectionStatus
            from aperag.service.quota_service import quota_service
            from aperag.utils.utils import utc_now

            # Get collection within transaction
            stmt = select(db_models.Collection).where(
                db_models.Collection.id == collection_id, db_models.Collection.user == user
            )
            result = await session.execute(stmt)
            collection_to_delete = result.scalars().first()

            if not collection_to_delete:
                return None

            # Mark collection as deleted
            collection_to_delete.status = CollectionStatus.DELETED
            collection_to_delete.gmt_deleted = utc_now()

            # Release quota within the same transaction
            await quota_service.release_quota(user, "max_collection_count", 1, session)

            await session.flush()
            await session.refresh(collection_to_delete)

            return collection_to_delete

        deleted_instance = await self.db_ops.execute_with_transaction(_delete_collection_with_quota)

        if deleted_instance:
            # Clean up related resources
            collection_delete_task.delay(collection_id)
            return await self.build_collection_response(deleted_instance)

        return None

    async def execute_search_flow(
        self,
        data: view_models.SearchRequest,
        collection_id: str,
        search_user_id: str,
        chat_id: Optional[str] = None,
        flow_name: str = "search",
        flow_title: str = "Search",
    ) -> Tuple[List[SearchResultItem], str]:  # 对特定知识库执行检索逻辑
        """
        参数说明：
            search_user_id：当前用户信息【进行检索操作的人】
            collection_id：知识库id
            data：检索参数
                query: 用户问题
                vector_search: 向量检索
                    top_k：取前top_k个分段
                    similarity：相似度阈值
                fulltext_search: 全文检索
                    top_k：取前top_k个分段
                    keywords：从用户问题提取到的关键词？【用于关键词检索】
                graph_search: 知识图谱检索
                    top_k：取前top_k个结果
                summary_search: 摘要检索
                    top_k：取前top_k个分段
                    similarity：相似度阈值
                vision_search: 视觉信息检索
                    top_k：取前top_k个分段
                    similarity：相似度阈值
                save_to_history: 是否持久化检索结果
                rerank: 是否使用重排
        """
        """
        Execute search flow and return search result items and rerank node ID.

        Args:
            data: Search request data
            collection_id: Target collection ID for search
            search_user_id: User ID to use for search operations (may differ from requester for marketplace collections)
            chat_id: Optional chat ID for filtering in chat searches
            flow_name: Name of the flow instance
            flow_title: Title of the flow instance

        Returns:
            Tuple of (search result items, rerank node id)
        """
        from aperag.service.default_model_service import default_model_service
        # -- 创建检索流程
        # Build flow for search execution
        nodes = {}
        edges = []
        merge_node_id = "merge"  # 每一步索引检索的目标节点--merge
        merge_node_values = {
            "merge_strategy": "union",
            "deduplicate": True,
        }
        query = data.query  # 用户问题
        # Configure search nodes based on request
        if data.vector_search:  # 向量检索
            node_id = "vector_search"
            input_values = {
                "query": query,
                "top_k": data.vector_search.topk if data.vector_search else 5,
                "similarity_threshold": data.vector_search.similarity if data.vector_search else 0.2,
                "collection_ids": [collection_id],
            }
            # Add chat_id for filtering if provided
            if chat_id:
                input_values["chat_id"] = chat_id

            nodes[node_id] = NodeInstance(
                id=node_id,
                type="vector_search",
                input_values=input_values,
            )  # 收集向量检索节点
            merge_node_values["vector_search_docs"] = "{{ nodes.vector_search.output.docs }}"  # 对于向量检索结果，merge节点的处理变量路径
            edges.append(Edge(source=node_id, target=merge_node_id))  # 设置流程关系【起始节点：向量检索，目标节点：merge】

        if data.fulltext_search:  # 全文检索
            node_id = "fulltext_search"
            input_values = {
                "query": query,
                "top_k": data.fulltext_search.topk if data.fulltext_search else 5,
                "collection_ids": [collection_id],
                "keywords": data.fulltext_search.keywords,
            }
            # Add chat_id for filtering if provided
            if chat_id:
                input_values["chat_id"] = chat_id

            nodes[node_id] = NodeInstance(
                id=node_id,
                type="fulltext_search",
                input_values=input_values,
            )  # 收集全文检索节点
            merge_node_values["fulltext_search_docs"] = "{{ nodes.fulltext_search.output.docs }}"  # 对于全文检索结果，merge节点的处理变量路径
            edges.append(Edge(source=node_id, target=merge_node_id))  # 设置流程关系【起始节点：全文检索，目标节点：merge】

        if data.graph_search:  # 知识图谱检索
            input_values = {
                "query": query,
                "top_k": data.graph_search.topk if data.graph_search else 5,
                "collection_ids": [collection_id],
            }
            # Add chat_id for filtering if provided
            if chat_id:
                input_values["chat_id"] = chat_id

            nodes["graph_search"] = NodeInstance(
                id="graph_search",
                type="graph_search",
                input_values=input_values,
            )  # 收集知识图谱检索节点
            merge_node_values["graph_search_docs"] = "{{ nodes.graph_search.output.docs }}"  # 对于知识图谱检索结果，merge节点的处理变量路径
            edges.append(Edge(source="graph_search", target=merge_node_id))  # 设置流程关系【起始节点：知识图谱检索，目标节点：merge】

        if data.summary_search:  # 摘要检索
            node_id = "summary_search"
            input_values = {
                "query": query,
                "top_k": data.summary_search.topk if data.summary_search else 5,
                "similarity_threshold": data.summary_search.similarity if data.summary_search else 0.2,
                "collection_ids": [collection_id],
            }
            # Add chat_id for filtering if provided
            if chat_id:
                input_values["chat_id"] = chat_id

            nodes[node_id] = NodeInstance(
                id=node_id,
                type="summary_search",
                input_values=input_values,
            )  # 收集摘要检索节点
            merge_node_values["summary_search_docs"] = "{{ nodes.summary_search.output.docs }}"  # 对于摘要检索结果，merge节点的处理变量路径
            edges.append(Edge(source=node_id, target=merge_node_id))  # 设置流程关系【起始节点：摘要检索，目标节点：merge】

        if data.vision_search:  # 视觉信息检索
            node_id = "vision_search"
            input_values = {
                "query": query,
                "top_k": data.vision_search.topk if data.vision_search else 5,
                "similarity_threshold": data.vision_search.similarity if data.vision_search else 0.2,
                "collection_ids": [collection_id],
            }
            # Add chat_id for filtering if provided
            if chat_id:
                input_values["chat_id"] = chat_id

            nodes[node_id] = NodeInstance(
                id=node_id,
                type="vision_search",
                input_values=input_values,
            )  # 收集视觉信息检索节点
            merge_node_values["vision_search_docs"] = "{{ nodes.vision_search.output.docs }}"  # 对于视觉信息检索结果，merge节点的处理变量路径
            edges.append(Edge(source=node_id, target=merge_node_id))  # 设置流程关系【起始节点：视觉信息检索，目标节点：merge】

        nodes[merge_node_id] = NodeInstance(
            id=merge_node_id,
            type="merge",
            input_values=merge_node_values,
        )  # 收集merge节点
        # 基于重排标识和重排模型配置情况，设置重排服务可用标识use_rerank_service
        # Add rerank node to flow
        if data.rerank:  # 重排操作
            model, model_service_provider, custom_llm_provider = await default_model_service.get_default_rerank_config(
                search_user_id
            )
            use_rerank_service = model is not None
        else:
            model, model_service_provider, custom_llm_provider = None, None, None
            use_rerank_service = False

        rerank_node_id = "rerank"
        nodes[rerank_node_id] = NodeInstance(
            id=rerank_node_id,
            type="rerank",
            input_values={
                "use_rerank_service": use_rerank_service,
                "model": model,
                "model_service_provider": model_service_provider,
                "custom_llm_provider": custom_llm_provider,
                "docs": "{{ nodes.merge.output.docs }}",
            },
        )  # 收集重排节点
        # Add edge from merge to rerank
        edges.append(Edge(source=merge_node_id, target=rerank_node_id))  # 设置流程关系【起始节点：merge，目标节点：重排节点】
        # -- 执行检索流程
        # Execute search flow
        flow = FlowInstance(
            name=flow_name,
            title=flow_title,
            nodes=nodes,  # 见aperag.flow.base.models.NodeInstance
            edges=edges,  # 见aperag.flow.base.models.Edge
        )  # 基于节点集合和关系集合创建工作流【见aperag.flow.base.models.FlowInstance】
        engine = FlowEngine()  # 初始化流程引擎
        # Build initial data with chat_id if provided
        initial_data = {"query": query, "user": search_user_id}  # 初始化流程入参
        if chat_id:
            initial_data["chat_id"] = chat_id
        result, _ = await engine.execute_flow(flow, initial_data)  # 执行流程【见aperag.flow.engine.FlowEngine.execute_flow】 TODO 至此~

        if not result:
            raise Exception("Failed to execute flow")
        # -- 解析检索流程执行结果
        # Process search results from rerank node
        docs = result.get(rerank_node_id, {}).docs
        items = []
        for idx, doc in enumerate(docs):
            items.append(
                SearchResultItem(
                    rank=idx + 1,
                    score=doc.score,
                    content=doc.text,
                    source=doc.metadata.get("source", ""),
                    recall_type=doc.metadata.get("recall_type", ""),
                    metadata=doc.metadata,
                )
            )

        return items, rerank_node_id

    async def create_search(
        self, user: str, collection_id: str, data: view_models.SearchRequest
    ) -> view_models.SearchResult:  # 对单个知识库的混合检索操作
        """
        参数说明：
            user：当前用户信息
            collection_id：知识库id
            data：检索参数
                query: 用户问题
                vector_search: 向量检索
                    top_k：取前top_k个分段
                    similarity：相似度阈值
                fulltext_search: 全文检索
                    top_k：取前top_k个分段
                    keywords：从用户问题提取到的关键词？【用于关键词检索】
                graph_search: 知识图谱检索
                    top_k：取前top_k个结果
                summary_search: 摘要检索
                    top_k：取前top_k个分段
                    similarity：相似度阈值
                vision_search: 视觉信息检索
                    top_k：取前top_k个分段
                    similarity：相似度阈值
                save_to_history: 是否持久化检索结果
                rerank: 是否使用重排
        """
        from aperag.exceptions import CollectionNotFoundException
        # -- 校验当前知识库是否对于当前用户可用【不可用，则抛出CollectionNotFoundException】
        # Try to find collection as owner first
        collection = await self.db_ops.query_collection(user, collection_id)
        search_user_id = user  # Default to current user for search operations

        if not collection:
            # If not found as owner, check if it's a marketplace collection
            try:
                marketplace_info = await marketplace_collection_service._check_marketplace_access(user, collection_id)
                # Use owner's user_id for search operations in marketplace collections
                search_user_id = marketplace_info["owner_user_id"]
                collection = await self.db_ops.query_collection(search_user_id, collection_id)
                if not collection:
                    raise CollectionNotFoundException(collection_id)
            except Exception:
                # If marketplace access also fails, raise original not found error
                raise CollectionNotFoundException(collection_id)
        # -- 执行检索逻辑
        # Execute search flow using helper method
        items, _ = await self.execute_search_flow(
            data=data,
            collection_id=collection_id,
            search_user_id=search_user_id,
            chat_id=None,  # No chat filtering for regular collection searches
            flow_name="search",
            flow_title="Search",
        )
        # -- 根据save_to_history决定是否持久化检索数据【用户、用户问题、知识库id、各类索引检索参数详情、检索结果】。封装检索结果并返回
        # Save to database only if save_to_history is True
        if data.save_to_history:
            record = await self.db_ops.create_search(
                user=user,
                collection_id=collection_id,
                query=data.query,
                vector_search=data.vector_search.model_dump() if data.vector_search else None,
                fulltext_search=data.fulltext_search.model_dump() if data.fulltext_search else None,
                graph_search=data.graph_search.model_dump() if data.graph_search else None,
                summary_search=data.summary_search.model_dump() if data.summary_search else None,
                vision_search=data.vision_search.model_dump() if data.vision_search else None,
                items=[item.model_dump() for item in items],
            )
            return SearchResult(
                id=record.id,
                query=record.query,
                vector_search=record.vector_search,
                fulltext_search=record.fulltext_search,
                graph_search=record.graph_search,
                summary_search=record.summary_search,
                vision_search=record.vision_search,
                items=items,
                created=record.gmt_created.isoformat(),
            )
        else:
            # Return search result without saving to database
            return SearchResult(
                id=None,  # No ID since not saved
                query=data.query,
                vector_search=data.vector_search,
                fulltext_search=data.fulltext_search,
                graph_search=data.graph_search,
                summary_search=data.summary_search,
                vision_search=data.vision_search,
                items=items,
                created=None,  # No creation time since not saved
            )

    async def list_searches(self, user: str, collection_id: str) -> view_models.SearchResultList:
        from aperag.exceptions import CollectionNotFoundException

        collection = await self.db_ops.query_collection(user, collection_id)
        if not collection:
            raise CollectionNotFoundException(collection_id)

        # Use DatabaseOps to query searches
        searches = await self.db_ops.query_searches(user, collection_id)

        items = []
        for search in searches:
            search_result_items = []
            for item_data in search.items:
                search_result_items.append(SearchResultItem(**item_data))
            items.append(
                SearchResult(
                    id=search.id,
                    query=search.query,
                    vector_search=search.vector_search,
                    fulltext_search=search.fulltext_search,
                    graph_search=search.graph_search,
                    summary_search=search.summary_search,
                    items=search_result_items,
                    created=search.gmt_created.isoformat(),
                )
            )
        return SearchResultList(items=items)

    async def delete_search(self, user: str, collection_id: str, search_id: str) -> Optional[bool]:
        """Delete search by ID (idempotent operation)

        Returns True if deleted, None if already deleted/not found
        """
        from aperag.exceptions import CollectionNotFoundException

        collection = await self.db_ops.query_collection(user, collection_id)
        if not collection:
            raise CollectionNotFoundException(collection_id)

        return await self.db_ops.delete_search(user, collection_id, search_id)

    async def validate_collections_batch(
        self, user: str, collections: list[view_models.Collection]
    ) -> tuple[bool, str]:
        """
        Validate multiple collections in a single database call.

        Args:
            user: User identifier
            collections: List of collection objects to validate

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty.
        """
        if not collections:
            return True, ""

        # Extract collection IDs and validate they exist
        collection_ids = []
        for collection in collections:
            if not collection.id:
                return False, "Collection object missing 'id' field"
            collection_ids.append(collection.id)

        # Remove duplicates while preserving order
        unique_collection_ids = list(dict.fromkeys(collection_ids))

        try:
            # Single database call to get all collections
            db_collections = await self.db_ops.query_collections_by_ids(user, unique_collection_ids)

            # Create a set of found collection IDs for fast lookup
            found_collection_ids = {str(col.id) for col in db_collections}

            # Check if all requested collections were found
            for collection_id in unique_collection_ids:
                if collection_id not in found_collection_ids:
                    return False, f"Collection {collection_id} not found"

            return True, ""

        except Exception as e:
            return False, f"Failed to validate collections: {str(e)}"

    async def test_mineru_token(self, token: str) -> dict:
        """Test the MinerU API token."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://mineru.net/api/v4/extract-results/batch/test-token",
                    headers={"Authorization": f"Bearer {token}"},
                )
                return {"status_code": response.status_code, "data": response.json()}
            except httpx.RequestError as e:
                return {"status_code": 500, "data": {"msg": f"Request failed: {e}"}}


# Create a global service instance for easy access
# This uses the global db_ops instance and doesn't require session management in views
collection_service = CollectionService()
