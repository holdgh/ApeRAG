"""
Neo4j最优连接管理方案 - 利用官方驱动的内置连接池
"""
import os
import logging
from typing import Optional
from contextlib import contextmanager
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


class Neo4jConnectionManager:
    """
    利用Neo4j官方驱动内置连接池的最优方案
    """
    _sync_driver: Optional[GraphDatabase.driver] = None
    _async_driver: Optional[AsyncGraphDatabase.driver] = None
    
    @classmethod
    def get_sync_driver(cls):
        """获取同步驱动（用于Celery等同步环境）"""
        if cls._sync_driver is None:
            uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
            user = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            
            # Neo4j驱动配置 - 充分利用内置连接池
            cls._sync_driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
                # 连接池配置
                max_connection_pool_size=50,  # 最大连接数
                connection_acquisition_timeout=60.0,  # 获取连接超时（秒）
                
                # 连接生命周期
                max_connection_lifetime=3600,  # 连接最大生存时间（秒）
                connection_timeout=30.0,  # 连接超时
                
                # 安全和性能
                encrypted=True,  # 使用加密连接
                trust=GraphDatabase.TRUST_SYSTEM_CA_SIGNED_CERTIFICATES,
                
                # 其他优化
                user_agent="ApeRAG/1.0",  # 便于服务端识别
                
                # 连接池行为
                max_transaction_retry_time=30.0,  # 事务重试时间
                initial_retry_delay=1.0,
                retry_delay_multiplier=2.0,
                retry_delay_jitter_factor=0.2,
            )
            
            # 验证连接
            try:
                cls._sync_driver.verify_connectivity()
                logger.info("Neo4j sync driver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                cls._sync_driver = None
                raise
                
        return cls._sync_driver
    
    @classmethod
    async def get_async_driver(cls):
        """获取异步驱动（用于纯异步环境）"""
        if cls._async_driver is None:
            uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
            user = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            
            cls._async_driver = AsyncGraphDatabase.driver(
                uri,
                auth=(user, password),
                # 与同步驱动相同的配置
                max_connection_pool_size=50,
                connection_acquisition_timeout=60.0,
                max_connection_lifetime=3600,
                connection_timeout=30.0,
                encrypted=True,
                trust=AsyncGraphDatabase.TRUST_SYSTEM_CA_SIGNED_CERTIFICATES,
            )
            
            # 异步验证连接
            try:
                await cls._async_driver.verify_connectivity()
                logger.info("Neo4j async driver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                cls._async_driver = None
                raise
                
        return cls._async_driver
    
    @classmethod
    def close_sync_driver(cls):
        """关闭同步驱动"""
        if cls._sync_driver:
            cls._sync_driver.close()
            cls._sync_driver = None
            logger.info("Neo4j sync driver closed")
    
    @classmethod
    async def close_async_driver(cls):
        """关闭异步驱动"""
        if cls._async_driver:
            await cls._async_driver.close()
            cls._async_driver = None
            logger.info("Neo4j async driver closed")
    
    @classmethod
    def get_pool_metrics(cls):
        """获取连接池指标（用于监控）"""
        metrics = {}
        
        if cls._sync_driver:
            # 注意：具体的指标API可能因版本而异
            # 这里展示概念
            metrics['sync'] = {
                'in_use': getattr(cls._sync_driver, '_pool_in_use', 'N/A'),
                'idle': getattr(cls._sync_driver, '_pool_idle', 'N/A'),
            }
            
        if cls._async_driver:
            metrics['async'] = {
                'in_use': getattr(cls._async_driver, '_pool_in_use', 'N/A'),
                'idle': getattr(cls._async_driver, '_pool_idle', 'N/A'),
            }
            
        return metrics


# Celery集成示例
def setup_celery_neo4j(app):
    """配置Celery使用Neo4j"""
    from celery.signals import worker_process_init, worker_process_shutdown
    
    @worker_process_init.connect
    def init_worker(**kwargs):
        """Worker启动时初始化驱动"""
        try:
            Neo4jConnectionManager.get_sync_driver()
            logger.info("Neo4j driver initialized for worker")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            raise
    
    @worker_process_shutdown.connect
    def shutdown_worker(**kwargs):
        """Worker关闭时清理驱动"""
        Neo4jConnectionManager.close_sync_driver()


# 使用示例
class Neo4jService:
    """展示如何使用内置连接池的服务类"""
    
    @staticmethod
    def execute_query(query: str, parameters: dict = None):
        """执行查询 - 同步版本"""
        driver = Neo4jConnectionManager.get_sync_driver()
        
        # 使用session - 轻量级，可以随意创建
        with driver.session() as session:
            # 使用事务函数 - 自动重试
            def work(tx):
                result = tx.run(query, parameters or {})
                return list(result)
            
            # 根据查询类型选择读/写事务
            if query.strip().upper().startswith(('CREATE', 'MERGE', 'DELETE', 'SET')):
                return session.write_transaction(work)
            else:
                return session.read_transaction(work)
    
    @staticmethod
    async def execute_query_async(query: str, parameters: dict = None):
        """执行查询 - 异步版本"""
        driver = await Neo4jConnectionManager.get_async_driver()
        
        async with driver.session() as session:
            async def work(tx):
                result = await tx.run(query, parameters or {})
                return await result.data()
            
            if query.strip().upper().startswith(('CREATE', 'MERGE', 'DELETE', 'SET')):
                return await session.execute_write(work)
            else:
                return await session.execute_read(work)
    
    @staticmethod
    @contextmanager
    def batch_session():
        """批量操作的session上下文"""
        driver = Neo4jConnectionManager.get_sync_driver()
        session = driver.session()
        try:
            yield session
        finally:
            session.close()


# 在LightRAG中使用
class LightRAGNeo4jAdapter:
    """适配LightRAG使用官方驱动连接池"""
    
    def __init__(self):
        self.driver = Neo4jConnectionManager.get_sync_driver()
    
    def execute_in_thread(self, query: str, parameters: dict = None):
        """在线程中执行（供异步代码调用）"""
        import asyncio
        
        # 使用asyncio.to_thread在后台线程执行同步操作
        return asyncio.to_thread(
            Neo4jService.execute_query,
            query,
            parameters
        )
    
    async def query(self, cypher: str, params: dict = None):
        """异步查询接口"""
        # 选项1：使用同步驱动 + to_thread
        return await self.execute_in_thread(cypher, params)
        
        # 选项2：使用异步驱动（如果在纯异步环境）
        # return await Neo4jService.execute_query_async(cypher, params)


# 监控示例
def log_connection_pool_stats():
    """记录连接池状态"""
    metrics = Neo4jConnectionManager.get_pool_metrics()
    logger.info(f"Neo4j connection pool metrics: {metrics}")


# Celery任务示例
from celery import Celery

app = Celery('tasks')
setup_celery_neo4j(app)

@app.task
def process_graph_data(data):
    """Celery任务直接使用驱动"""
    # 驱动已在Worker启动时初始化，直接使用即可
    results = Neo4jService.execute_query(
        "MATCH (n:Node {id: $id}) RETURN n",
        {"id": data["id"]}
    )
    return results 