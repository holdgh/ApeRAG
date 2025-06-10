"""
Neo4j异步连接管理器 - 为Prefect等异步任务队列优化

核心设计：
1. 每个事件循环拥有独立的Neo4j异步驱动实例
2. 使用弱引用自动清理不再使用的事件循环的驱动
3. 线程安全的驱动注册表
"""
import asyncio
import os
import logging
import weakref
import threading
from typing import Dict, Optional, Any
from contextvars import ContextVar

from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired

logger = logging.getLogger(__name__)


# Context变量，用于在异步上下文中传递驱动
_driver_context: ContextVar[Optional['AsyncGraphDatabase.driver']] = ContextVar(
    'neo4j_async_driver', 
    default=None
)


class EventLoopDriverRegistry:
    """
    事件循环级别的Neo4j驱动注册表
    每个事件循环都有自己的驱动实例，避免跨事件循环共享连接
    """
    
    def __init__(self):
        # 使用弱引用字典，当事件循环被垃圾回收时自动清理驱动
        self._drivers: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, AsyncGraphDatabase.driver] = (
            weakref.WeakKeyDictionary()
        )
        # 线程锁保护注册表的并发访问
        self._lock = threading.Lock()
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载Neo4j配置"""
        return {
            'uri': os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            'auth': (
                os.getenv("NEO4J_USERNAME", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "password")
            ),
            'max_connection_pool_size': int(os.getenv("NEO4J_MAX_POOL_SIZE", "50")),
            'connection_acquisition_timeout': float(os.getenv("NEO4J_CONN_TIMEOUT", "60.0")),
            'max_connection_lifetime': 3600,
            'connection_timeout': 30.0,
            'keep_alive': True,
            'encrypted': os.getenv("NEO4J_ENCRYPTED", "true").lower() == "true",
            'trust': AsyncGraphDatabase.TRUST_SYSTEM_CA_SIGNED_CERTIFICATES,
        }
    
    async def get_driver(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> AsyncGraphDatabase.driver:
        """
        获取当前事件循环的驱动实例
        如果不存在则创建新的驱动
        """
        if loop is None:
            loop = asyncio.get_running_loop()
        
        # 快速路径：检查是否已有驱动
        driver = self._drivers.get(loop)
        if driver is not None:
            return driver
        
        # 慢路径：创建新驱动（需要加锁）
        with self._lock:
            # 双重检查
            driver = self._drivers.get(loop)
            if driver is not None:
                return driver
            
            # 创建新驱动
            logger.info(f"Creating new Neo4j driver for event loop {id(loop)}")
            driver = await self._create_driver()
            
            # 注册驱动
            self._drivers[loop] = driver
            
            # 注册清理回调（当事件循环关闭时）
            self._register_cleanup(loop, driver)
            
            return driver
    
    async def _create_driver(self) -> AsyncGraphDatabase.driver:
        """创建新的Neo4j驱动实例"""
        driver = AsyncGraphDatabase.driver(
            self._config['uri'],
            auth=self._config['auth'],
            max_connection_pool_size=self._config['max_connection_pool_size'],
            connection_acquisition_timeout=self._config['connection_acquisition_timeout'],
            max_connection_lifetime=self._config['max_connection_lifetime'],
            connection_timeout=self._config['connection_timeout'],
            keep_alive=self._config['keep_alive'],
            encrypted=self._config['encrypted'],
            trust=self._config['trust'],
            user_agent="ApeRAG-Async/1.0",
        )
        
        # 验证连接
        try:
            await driver.verify_connectivity()
            logger.info("Neo4j async driver created and verified successfully")
        except Exception as e:
            logger.error(f"Failed to verify Neo4j connectivity: {e}")
            await driver.close()
            raise
        
        return driver
    
    def _register_cleanup(self, loop: asyncio.AbstractEventLoop, driver: AsyncGraphDatabase.driver):
        """注册驱动清理回调"""
        def cleanup():
            logger.info(f"Cleaning up Neo4j driver for event loop {id(loop)}")
            # 在事件循环中调度异步清理
            asyncio.run_coroutine_threadsafe(driver.close(), loop)
        
        # 使用弱引用回调，当loop被垃圾回收时自动调用
        weakref.finalize(loop, cleanup)
    
    async def close_all(self):
        """关闭所有驱动（用于优雅关闭）"""
        with self._lock:
            drivers = list(self._drivers.values())
        
        for driver in drivers:
            try:
                await driver.close()
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                'active_event_loops': len(self._drivers),
                'event_loop_ids': [id(loop) for loop in self._drivers.keys()],
            }


# 全局注册表实例
_registry = EventLoopDriverRegistry()


class Neo4jAsyncConnectionManager:
    """
    Neo4j异步连接管理器 - 面向Prefect等异步任务队列
    
    使用方式：
    1. 在任务中直接使用 get_driver() 获取当前事件循环的驱动
    2. 驱动会自动管理连接池
    3. 当事件循环结束时自动清理
    """
    
    @classmethod
    async def get_driver(cls) -> AsyncGraphDatabase.driver:
        """获取当前事件循环的Neo4j驱动"""
        # 优先使用上下文变量中的驱动
        driver = _driver_context.get()
        if driver is not None:
            return driver
        
        # 从注册表获取或创建驱动
        driver = await _registry.get_driver()
        _driver_context.set(driver)
        return driver
    
    @classmethod
    async def execute_query(cls, query: str, parameters: Dict[str, Any] = None, 
                          database: str = None) -> list:
        """
        执行查询的便捷方法
        
        Args:
            query: Cypher查询
            parameters: 查询参数
            database: 数据库名称（可选）
        
        Returns:
            查询结果列表
        """
        driver = await cls.get_driver()
        
        async with driver.session(database=database) as session:
            # 判断是读还是写操作
            is_write = any(
                query.strip().upper().startswith(cmd) 
                for cmd in ('CREATE', 'MERGE', 'DELETE', 'SET', 'REMOVE')
            )
            
            if is_write:
                return await session.execute_write(
                    cls._execute_transaction, query, parameters
                )
            else:
                return await session.execute_read(
                    cls._execute_transaction, query, parameters
                )
    
    @staticmethod
    async def _execute_transaction(tx, query: str, parameters: Dict[str, Any] = None):
        """事务执行函数"""
        result = await tx.run(query, parameters or {})
        return await result.data()
    
    @classmethod
    async def get_stats(cls) -> Dict[str, Any]:
        """获取连接管理器统计信息"""
        return _registry.get_stats()
    
    @classmethod
    async def close_all(cls):
        """关闭所有驱动（通常在应用关闭时调用）"""
        await _registry.close_all()


# Prefect集成示例
async def setup_prefect_neo4j():
    """
    Prefect启动时的设置（可选）
    Prefect会自动管理事件循环，所以通常不需要特殊设置
    """
    # 预热：在主事件循环中创建驱动
    await Neo4jAsyncConnectionManager.get_driver()
    logger.info("Neo4j async driver initialized for Prefect")


# 任务装饰器（可选）- 自动注入Neo4j会话
def with_neo4j_session(database: str = None):
    """
    装饰器：自动为Prefect任务注入Neo4j会话
    
    使用示例：
    @task
    @with_neo4j_session()
    async def my_task(session: AsyncSession, data: dict):
        result = await session.run("MATCH (n) RETURN n LIMIT 10")
        return await result.data()
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            driver = await Neo4jAsyncConnectionManager.get_driver()
            async with driver.session(database=database) as session:
                # 注入session到函数参数
                return await func(session=session, *args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator


# Prefect任务示例
from prefect import task, flow

@task
async def process_graph_data(node_id: str) -> dict:
    """Prefect任务示例 - 直接使用连接管理器"""
    results = await Neo4jAsyncConnectionManager.execute_query(
        "MATCH (n:Node {id: $id}) RETURN n",
        {"id": node_id}
    )
    return results[0] if results else None


@task
@with_neo4j_session()
async def batch_create_nodes(session, nodes: list) -> int:
    """Prefect任务示例 - 使用session装饰器"""
    tx_func = lambda tx: tx.run(
        "UNWIND $nodes AS node CREATE (n:Node) SET n = node",
        nodes=nodes
    )
    
    result = await session.execute_write(tx_func)
    summary = await result.consume()
    return summary.counters.nodes_created


@flow
async def graph_processing_flow(node_ids: list):
    """Prefect流程示例"""
    # 并发处理多个节点
    results = await asyncio.gather(*[
        process_graph_data(node_id) for node_id in node_ids
    ])
    
    # 批量创建新节点
    new_nodes = [{"id": f"new_{i}", "data": r} for i, r in enumerate(results) if r]
    if new_nodes:
        count = await batch_create_nodes(new_nodes)
        logger.info(f"Created {count} new nodes")
    
    return results


# 用于LightRAG的适配器
class LightRAGAsyncNeo4jAdapter:
    """
    适配LightRAG使用异步Neo4j连接管理器
    为Prefect环境优化
    """
    
    async def initialize(self):
        """初始化（预热驱动）"""
        await Neo4jAsyncConnectionManager.get_driver()
    
    async def query(self, cypher: str, params: Dict[str, Any] = None) -> list:
        """执行查询"""
        return await Neo4jAsyncConnectionManager.execute_query(cypher, params)
    
    async def execute_write(self, cypher: str, params: Dict[str, Any] = None) -> Any:
        """执行写操作"""
        driver = await Neo4jAsyncConnectionManager.get_driver()
        
        async with driver.session() as session:
            async def work(tx):
                result = await tx.run(cypher, params or {})
                # 对于写操作，通常返回summary
                return await result.consume()
            
            summary = await session.execute_write(work)
            return {
                'nodes_created': summary.counters.nodes_created,
                'relationships_created': summary.counters.relationships_created,
                'properties_set': summary.counters.properties_set,
            }
    
    async def close(self):
        """关闭（通常不需要调用，自动管理）"""
        # 驱动会随事件循环自动清理
        pass


# 监控和调试工具
async def log_neo4j_stats():
    """记录Neo4j连接统计"""
    stats = await Neo4jAsyncConnectionManager.get_stats()
    logger.info(f"Neo4j async connection stats: {stats}")


# 错误处理示例
@task(retries=3, retry_delay_seconds=5)
async def resilient_graph_query(query: str) -> list:
    """带重试的弹性查询"""
    try:
        return await Neo4jAsyncConnectionManager.execute_query(query)
    except (ServiceUnavailable, SessionExpired) as e:
        logger.warning(f"Neo4j connection error, will retry: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in graph query: {e}")
        raise 