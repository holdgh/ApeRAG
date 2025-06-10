"""
Neo4j混合实现 - 同时支持同步（Celery）和异步（Prefect）模式

根据环境自动选择：
- Celery环境：使用同步驱动
- Prefect环境：使用异步驱动
"""
import inspect
import logging
import os
from dataclasses import dataclass
from typing import final, Optional
import asyncio

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..base import BaseGraphStorage
from ..types import KnowledgeGraph, KnowledgeGraphEdge, KnowledgeGraphNode
from ..utils import logger

from dotenv import load_dotenv
from neo4j import exceptions as neo4jExceptions

# Import both sync and async connection managers
try:
    from aperag.db.neo4j_sync_manager import Neo4jSyncConnectionManager
except ImportError:
    Neo4jSyncConnectionManager = None

try:
    from aperag.db.neo4j_async_manager import Neo4jAsyncConnectionManager
except ImportError:
    Neo4jAsyncConnectionManager = None

# Load environment variables
load_dotenv(dotenv_path=".env", override=False)

# Get maximum number of graph nodes from environment variable
MAX_GRAPH_NODES = int(os.getenv("MAX_GRAPH_NODES", 1000))

# Set neo4j logger level to ERROR to suppress warning logs
logging.getLogger("neo4j").setLevel(logging.ERROR)


def detect_execution_environment():
    """
    检测当前执行环境
    
    Returns:
        "celery": 在Celery任务中
        "prefect": 在Prefect任务中
        "async": 在异步环境中
        "sync": 在同步环境中
    """
    # 检查是否在Celery任务中
    try:
        from celery import current_task
        if current_task is not None:
            return "celery"
    except ImportError:
        pass
    
    # 检查是否在Prefect任务中
    try:
        from prefect.context import get_run_context
        try:
            get_run_context()
            return "prefect"
        except RuntimeError:
            pass
    except ImportError:
        pass
    
    # 检查是否在异步环境中
    try:
        asyncio.get_running_loop()
        return "async"
    except RuntimeError:
        return "sync"


@final
@dataclass
class Neo4JHybridStorage(BaseGraphStorage):
    """
    混合Neo4j存储实现
    根据运行环境自动选择同步或异步驱动
    """
    
    def __init__(self, namespace, workspace, global_config, embedding_func):
        super().__init__(
            namespace=namespace,
            workspace=workspace,
            global_config=global_config,
            embedding_func=embedding_func,
        )
        self._driver = None
        self._session = None
        self._DATABASE = None
        self._mode = None  # "sync" or "async"
        self._initialized = False
    
    async def initialize(self):
        """初始化存储，根据环境选择合适的连接管理器"""
        if self._initialized:
            return
            
        env = detect_execution_environment()
        logger.info(f"Neo4JHybridStorage detected environment: {env}")
        
        if env == "celery":
            # Celery环境：使用同步驱动
            await self._initialize_sync_mode()
        elif env in ["prefect", "async"]:
            # Prefect或纯异步环境：使用异步驱动
            await self._initialize_async_mode()
        else:
            # 默认使用同步模式
            await self._initialize_sync_mode()
        
        self._initialized = True
    
    async def _initialize_sync_mode(self):
        """初始化同步模式"""
        if Neo4jSyncConnectionManager is None:
            raise RuntimeError("Sync Neo4j connection manager is not available")
        
        self._mode = "sync"
        
        # 获取同步驱动
        self._driver = Neo4jSyncConnectionManager.get_driver()
        
        # 在线程中执行同步操作
        def get_database():
            with self._driver.session() as session:
                # 使用workspace作为数据库名称
                # 注意：这里假设数据库已经存在或自动创建
                return self.workspace
        
        self._DATABASE = await asyncio.to_thread(get_database)
        
        logger.info(
            f"Neo4JHybridStorage initialized in SYNC mode for workspace '{self.workspace}', "
            f"database '{self._DATABASE}'"
        )
    
    async def _initialize_async_mode(self):
        """初始化异步模式"""
        if Neo4jAsyncConnectionManager is None:
            raise RuntimeError("Async Neo4j connection manager is not available")
        
        self._mode = "async"
        
        # 获取异步驱动
        self._driver = await Neo4jAsyncConnectionManager.get_driver()
        
        # 使用workspace作为数据库名称
        self._DATABASE = self.workspace
        
        logger.info(
            f"Neo4JHybridStorage initialized in ASYNC mode for workspace '{self.workspace}', "
            f"database '{self._DATABASE}'"
        )
    
    async def finalize(self):
        """清理资源"""
        self._driver = None
        self._session = None
        self._initialized = False
        logger.debug(f"Neo4JHybridStorage finalized for workspace '{self.workspace}'")
    
    async def _execute_query(self, query: str, parameters: dict = None, mode: str = "READ"):
        """
        执行查询的统一接口，根据模式选择同步或异步执行
        
        Args:
            query: Cypher查询
            parameters: 查询参数
            mode: "READ" 或 "WRITE"
        
        Returns:
            查询结果
        """
        if not self._initialized:
            await self.initialize()
        
        if self._mode == "sync":
            # 同步模式：在线程中执行
            return await self._execute_sync_query(query, parameters, mode)
        else:
            # 异步模式：直接执行
            return await self._execute_async_query(query, parameters, mode)
    
    async def _execute_sync_query(self, query: str, parameters: dict = None, mode: str = "READ"):
        """在线程中执行同步查询"""
        def run_query():
            with self._driver.session(database=self._DATABASE, default_access_mode=mode) as session:
                if mode == "WRITE":
                    # 写操作使用事务
                    def work(tx):
                        result = tx.run(query, parameters or {})
                        # 对于写操作，返回summary
                        return list(result)
                    
                    return session.execute_write(work)
                else:
                    # 读操作
                    result = session.run(query, parameters or {})
                    return list(result)
        
        return await asyncio.to_thread(run_query)
    
    async def _execute_async_query(self, query: str, parameters: dict = None, mode: str = "READ"):
        """执行异步查询"""
        async with self._driver.session(database=self._DATABASE, default_access_mode=mode) as session:
            if mode == "WRITE":
                # 写操作使用事务
                async def work(tx):
                    result = await tx.run(query, parameters or {})
                    return await result.data()
                
                return await session.execute_write(work)
            else:
                # 读操作
                result = await session.run(query, parameters or {})
                return await result.data()
    
    # 以下是具体的存储方法实现
    # 这些方法都使用 _execute_query 统一接口
    
    async def has_node(self, node_id: str) -> bool:
        """检查节点是否存在"""
        query = "MATCH (n:base {entity_id: $entity_id}) RETURN count(n) > 0 AS node_exists"
        results = await self._execute_query(query, {"entity_id": node_id})
        return results[0]["node_exists"] if results else False
    
    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        """检查边是否存在"""
        query = (
            "MATCH (a:base {entity_id: $source_entity_id})-[r]-(b:base {entity_id: $target_entity_id}) "
            "RETURN COUNT(r) > 0 AS edgeExists"
        )
        results = await self._execute_query(
            query,
            {"source_entity_id": source_node_id, "target_entity_id": target_node_id}
        )
        return results[0]["edgeExists"] if results else False
    
    async def get_node(self, node_id: str) -> dict[str, str] | None:
        """获取节点"""
        query = "MATCH (n:base {entity_id: $entity_id}) RETURN n"
        results = await self._execute_query(query, {"entity_id": node_id})
        
        if results:
            node = results[0]["n"]
            # 处理node数据格式
            if isinstance(node, dict):
                return node
            else:
                # 如果是Node对象，转换为字典
                node_dict = dict(node) if hasattr(node, '__iter__') else node._properties
                return node_dict
        return None
    
    async def node_degree(self, node_id: str) -> int:
        """获取节点的度"""
        query = """
            MATCH (n:base {entity_id: $entity_id})
            OPTIONAL MATCH (n)-[r]-()
            RETURN COUNT(r) AS degree
        """
        results = await self._execute_query(query, {"entity_id": node_id})
        return results[0]["degree"] if results else 0
    
    async def get_edge(
        self, source_node_id: str, target_node_id: str
    ) -> dict[str, str] | None:
        """获取边"""
        query = """
        MATCH (start:base {entity_id: $source_entity_id})-[r]-(end:base {entity_id: $target_entity_id})
        RETURN properties(r) as edge_properties
        """
        results = await self._execute_query(
            query,
            {"source_entity_id": source_node_id, "target_entity_id": target_node_id}
        )
        
        if results:
            edge_props = results[0]["edge_properties"]
            # 确保必需的键存在
            for key, default in {
                "weight": 0.0,
                "source_id": None,
                "description": None,
                "keywords": None,
            }.items():
                if key not in edge_props:
                    edge_props[key] = default
            return edge_props
        return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (
                neo4jExceptions.ServiceUnavailable,
                neo4jExceptions.TransientError,
                neo4jExceptions.WriteServiceUnavailable,
                neo4jExceptions.ClientError,
            )
        ),
    )
    async def upsert_node(self, node_id: str, node_data: dict[str, str]) -> None:
        """插入或更新节点"""
        properties = node_data
        entity_type = properties.get("entity_type", "base")
        
        if "entity_id" not in properties:
            raise ValueError("Neo4j: node properties must contain an 'entity_id' field")
        
        query = f"""
        MERGE (n:base {{entity_id: $entity_id}})
        SET n += $properties
        SET n:`{entity_type}`
        """
        
        await self._execute_query(
            query,
            {"entity_id": node_id, "properties": properties},
            mode="WRITE"
        )
        logger.debug(f"Upserted node with entity_id '{node_id}'")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (
                neo4jExceptions.ServiceUnavailable,
                neo4jExceptions.TransientError,
                neo4jExceptions.WriteServiceUnavailable,
                neo4jExceptions.ClientError,
            )
        ),
    )
    async def upsert_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ) -> None:
        """插入或更新边"""
        query = """
        MATCH (source:base {entity_id: $source_entity_id})
        WITH source
        MATCH (target:base {entity_id: $target_entity_id})
        MERGE (source)-[r:DIRECTED]-(target)
        SET r += $properties
        RETURN r, source, target
        """
        
        await self._execute_query(
            query,
            {
                "source_entity_id": source_node_id,
                "target_entity_id": target_node_id,
                "properties": edge_data,
            },
            mode="WRITE"
        )
        logger.debug(f"Upserted edge from '{source_node_id}' to '{target_node_id}'")
    
    async def delete_node(self, node_id: str) -> None:
        """删除节点"""
        query = """
        MATCH (n:base {entity_id: $entity_id})
        DETACH DELETE n
        """
        await self._execute_query(query, {"entity_id": node_id}, mode="WRITE")
        logger.debug(f"Deleted node with entity_id '{node_id}'")
    
    async def get_all_labels(self) -> list[str]:
        """获取所有节点标签"""
        query = """
        MATCH (n:base)
        WHERE n.entity_id IS NOT NULL
        RETURN DISTINCT n.entity_id AS label
        ORDER BY label
        """
        results = await self._execute_query(query)
        return [record["label"] for record in results]
    
    async def drop(self) -> dict[str, str]:
        """删除所有数据"""
        try:
            query = "MATCH (n) DETACH DELETE n"
            await self._execute_query(query, mode="WRITE")
            logger.info(f"Dropped all data in database {self._DATABASE}")
            return {"status": "success", "message": "data dropped"}
        except Exception as e:
            logger.error(f"Error dropping database {self._DATABASE}: {e}")
            return {"status": "error", "message": str(e)}
    
    # 批量操作方法
    async def get_nodes_batch(self, node_ids: list[str]) -> dict[str, dict]:
        """批量获取节点"""
        query = """
        UNWIND $node_ids AS id
        MATCH (n:base {entity_id: id})
        RETURN n.entity_id AS entity_id, n
        """
        results = await self._execute_query(query, {"node_ids": node_ids})
        
        nodes = {}
        for record in results:
            entity_id = record["entity_id"]
            node = record["n"]
            # 处理node数据格式
            if isinstance(node, dict):
                nodes[entity_id] = node
            else:
                nodes[entity_id] = dict(node) if hasattr(node, '__iter__') else node._properties
        
        return nodes
    
    async def node_degrees_batch(self, node_ids: list[str]) -> dict[str, int]:
        """批量获取节点度"""
        query = """
        UNWIND $node_ids AS id
        MATCH (n:base {entity_id: id})
        RETURN n.entity_id AS entity_id, count { (n)--() } AS degree
        """
        results = await self._execute_query(query, {"node_ids": node_ids})
        
        degrees = {}
        for record in results:
            entity_id = record["entity_id"]
            degrees[entity_id] = record["degree"]
        
        # 对于未找到的节点，设置度为0
        for nid in node_ids:
            if nid not in degrees:
                degrees[nid] = 0
        
        return degrees
    
    # 简化其他必需的方法
    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        """获取边的度（两个节点的度之和）"""
        degrees = await self.node_degrees_batch([src_id, tgt_id])
        return degrees.get(src_id, 0) + degrees.get(tgt_id, 0)
    
    async def get_node_edges(self, source_node_id: str) -> list[tuple[str, str]] | None:
        """获取节点的所有边"""
        query = """
        MATCH (n:base {entity_id: $entity_id})
        OPTIONAL MATCH (n)-[r]-(connected:base)
        WHERE connected.entity_id IS NOT NULL
        RETURN n.entity_id as source, connected.entity_id as target
        """
        results = await self._execute_query(query, {"entity_id": source_node_id})
        
        edges = []
        for record in results:
            if record["target"]:
                edges.append((record["source"], record["target"]))
        
        return edges if edges else None
    
    # 图知识获取（简化版本）
    async def get_knowledge_graph(
        self,
        node_label: str,
        max_depth: int = 3,
        max_nodes: int = MAX_GRAPH_NODES,
    ) -> KnowledgeGraph:
        """获取知识图谱子图"""
        # 这是一个简化实现，实际使用时可能需要根据具体需求完善
        result = KnowledgeGraph()
        
        # 简单的BFS实现
        if node_label == "*":
            # 获取所有节点（限制数量）
            query = """
            MATCH (n)
            RETURN n
            LIMIT $limit
            """
            node_results = await self._execute_query(query, {"limit": max_nodes})
            
            for record in node_results:
                node = record["n"]
                node_data = dict(node) if hasattr(node, '__iter__') else node._properties
                result.nodes.append(
                    KnowledgeGraphNode(
                        id=node_data.get("entity_id", str(id(node))),
                        labels=[node_data.get("entity_id", "Unknown")],
                        properties=node_data,
                    )
                )
        else:
            # 从特定节点开始的子图
            # 使用简单的Cypher查询，不依赖APOC
            query = """
            MATCH path = (start:base {entity_id: $entity_id})-[*0..%d]-(connected)
            WITH start, connected, relationships(path) as rels
            LIMIT $limit
            RETURN collect(DISTINCT start) + collect(DISTINCT connected) as nodes,
                   collect(DISTINCT rels) as relationships
            """ % max_depth
            
            results = await self._execute_query(
                query,
                {"entity_id": node_label, "limit": max_nodes}
            )
            
            if results and results[0]["nodes"]:
                seen_nodes = set()
                for node in results[0]["nodes"]:
                    node_data = dict(node) if hasattr(node, '__iter__') else node._properties
                    node_id = node_data.get("entity_id", str(id(node)))
                    if node_id not in seen_nodes:
                        result.nodes.append(
                            KnowledgeGraphNode(
                                id=node_id,
                                labels=[node_id],
                                properties=node_data,
                            )
                        )
                        seen_nodes.add(node_id)
        
        return result
    
    # 批量删除方法
    async def remove_nodes(self, nodes: list[str]):
        """批量删除节点"""
        for node in nodes:
            await self.delete_node(node)
    
    async def remove_edges(self, edges: list[tuple[str, str]]):
        """批量删除边"""
        for source, target in edges:
            query = """
            MATCH (source:base {entity_id: $source_entity_id})-[r]-(target:base {entity_id: $target_entity_id})
            DELETE r
            """
            await self._execute_query(
                query,
                {"source_entity_id": source, "target_entity_id": target},
                mode="WRITE"
            )
    
    # 补充缺失的批量方法
    async def get_edges_batch(
        self, pairs: list[dict[str, str]]
    ) -> dict[tuple[str, str], dict]:
        """批量获取边的属性"""
        query = """
        UNWIND $pairs AS pair
        MATCH (start:base {entity_id: pair.src})-[r:DIRECTED]-(end:base {entity_id: pair.tgt})
        RETURN pair.src AS src_id, pair.tgt AS tgt_id, collect(properties(r)) AS edges
        """
        results = await self._execute_query(query, {"pairs": pairs})
        
        edges_dict = {}
        for record in results:
            src = record["src_id"]
            tgt = record["tgt_id"]
            edges = record["edges"]
            if edges and len(edges) > 0:
                edge_props = edges[0]  # 选择第一个边
                # 确保必需的键存在
                for key, default in {
                    "weight": 0.0,
                    "source_id": None,
                    "description": None,
                    "keywords": None,
                }.items():
                    if key not in edge_props:
                        edge_props[key] = default
                edges_dict[(src, tgt)] = edge_props
            else:
                # 没有找到边，设置默认属性
                edges_dict[(src, tgt)] = {
                    "weight": 0.0,
                    "source_id": None,
                    "description": None,
                    "keywords": None,
                }
        
        return edges_dict
    
    async def edge_degrees_batch(
        self, edge_pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], int]:
        """批量计算边的度（源节点和目标节点的度之和）"""
        # 收集所有唯一的节点ID
        unique_node_ids = set()
        for src, tgt in edge_pairs:
            unique_node_ids.add(src)
            unique_node_ids.add(tgt)
        
        # 批量获取所有节点的度
        degrees = await self.node_degrees_batch(list(unique_node_ids))
        
        # 计算每条边的度
        edge_degrees = {}
        for src, tgt in edge_pairs:
            edge_degrees[(src, tgt)] = degrees.get(src, 0) + degrees.get(tgt, 0)
        
        return edge_degrees
    
    async def get_nodes_edges_batch(
        self, node_ids: list[str]
    ) -> dict[str, list[tuple[str, str]]]:
        """批量获取多个节点的边"""
        query = """
        UNWIND $node_ids AS id
        MATCH (n:base {entity_id: id})
        OPTIONAL MATCH (n)-[r]-(connected:base)
        RETURN id AS queried_id, n.entity_id AS node_entity_id,
               connected.entity_id AS connected_entity_id,
               startNode(r).entity_id AS start_entity_id
        """
        results = await self._execute_query(query, {"node_ids": node_ids})
        
        # 初始化结果字典
        edges_dict = {node_id: [] for node_id in node_ids}
        
        # 处理结果
        for record in results:
            queried_id = record["queried_id"]
            node_entity_id = record["node_entity_id"]
            connected_entity_id = record["connected_entity_id"]
            start_entity_id = record["start_entity_id"]
            
            # 跳过没有连接的情况
            if not node_entity_id or not connected_entity_id:
                continue
            
            # 根据边的方向添加到结果中
            if start_entity_id == node_entity_id:
                # 出边：(queried_node -> connected_node)
                edges_dict[queried_id].append((node_entity_id, connected_entity_id))
            else:
                # 入边：(connected_node -> queried_node)
                edges_dict[queried_id].append((connected_entity_id, node_entity_id))
        
        return edges_dict
    
    # 其他必需的方法可以根据需要添加... 