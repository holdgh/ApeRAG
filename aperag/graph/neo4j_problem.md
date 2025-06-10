你说得对，正常使用数据库，连接和操作都应该能正常结束。你感觉我的方案像是在"绕过"问题，而不是解决问题，这个直觉非常敏锐。

## 问题描述

在 `process_document_sync` 的 `finally` 块中，`loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))` 会一直卡住。通过调试发现有74个挂起任务，包括：

- `BaseSelectorEventLoop.sock_connect()` 任务
- `Neo4JStorage.initialize()` 任务
- `priority_limit_async_func_call` 的 `worker` 任务

## 根本原因

问题的根源是 **Neo4j 驱动程序为了维护连接池，自己启动了独立的后台任务**。这些后台任务被设计为 **"永久运行"** 的，包括：

1. **连接保活（Keep-alive）**：定期向服务器发送心跳包，防止连接因闲置而被防火墙或数据库关闭。
2. **路由表刷新**：在集群环境中，定期查询服务器的拓扑结构，确保总能连接到合适的节点。
3. **连接池管理**：监控池中连接的健康状况，创建新连接或关闭空闲连接。

### 代码执行链条分析

现在我们把这个背景和你的代码执行流程串起来：

1. **Celery 任务入口**: `add_lightrag_index_task` 调用 `process_document_for_celery`。
2. **创建临时事件循环**: `process_document_for_celery` 里的 `process_document_sync` 第一件事就是 `loop = asyncio.new_event_loop()`。
3. **LightRAG 处理**: 在这个临时循环中运行 `process_document_async`，里面会调用各种 LightRAG 方法。
4. **Neo4j 连接**: 当 LightRAG 需要 Neo4j 时，`Neo4JStorage.initialize()` 会创建一个 `AsyncDriver` 实例。
5. **后台任务启动**: Neo4j Driver 一旦创建，就会在当前事件循环（也就是我们的临时循环）中启动后台的心跳和路由刷新任务。
6. **业务逻辑完成**: 你的文档处理逻辑完成，函数准备返回。
7. **临时循环清理**: `process_document_sync` 的 `finally` 块尝试 "负责任地" 等待所有挂起任务完成再关闭循环。
8. **无限等待**: 但那些 Neo4j 的后台任务永远不会自然结束，所以 `gather(*pending)` 永远等下去。

这就是你看到的 74 个挂起任务的来源，也是为什么会卡死的原因。

## 最佳解决方案：全局共享的 Neo4j Driver ✓ IMPLEMENTED

这个方案的核心思想是将 Neo4j Driver 的生命周期与应用程序（或 Celery Worker 进程）的生命周期绑定，而不是与单个 `LightRAG` 实例或 Celery 任务绑定。

### 1. 创建全局 Driver 管理器 ✓

已创建 `aperag/db/neo4j_manager.py`，使用惰性加载锁避免事件循环冲突：

```python
class Neo4jDriverManager:
    _driver: Optional[AsyncDriver] = None
    _lock: Optional[asyncio.Lock] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """惰性加载锁，确保它在正确的事件循环中被创建。"""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    async def get_driver(cls) -> AsyncDriver:
        """获取全局共享的 Neo4j Driver 实例，如果不存在则初始化。"""
        if cls._driver is None:
            lock = cls._get_lock()
            async with lock:
                if cls._driver is None:
                    cls._driver = await cls._create_driver()
        return cls._driver

    @classmethod
    async def prepare_neo4j_database(cls, workspace: str) -> str:
        """Prepare Neo4j database (create database and indexes if needed)"""
        driver = await cls.get_driver()
        
        DATABASE = os.environ.get(
            "NEO4J_DATABASE", re.sub(r"[^a-zA-Z0-9-]", "-", workspace)
        )
        
        # Try to connect to the database and create it if it doesn't exist
        for database in (DATABASE, None):
            connected = False
            try:
                async with driver.session(database=database) as session:
                    try:
                        result = await session.run("MATCH (n) RETURN n LIMIT 0")
                        await result.consume()
                        logger.info(f"Connected to {database}")
                        connected = True
                    except neo4jExceptions.ServiceUnavailable as e:
                        logger.error(f"{database} is not available")
                        raise e
            except neo4jExceptions.AuthError as e:
                logger.error(f"Authentication failed for {database}")
                raise e
            except neo4jExceptions.ClientError as e:
                if e.code == "Neo.ClientError.Database.DatabaseNotFound":
                    logger.info(f"{database} not found. Try to create specified database.")
                    try:
                        async with driver.session() as session:
                            result = await session.run(
                                f"CREATE DATABASE `{database}` IF NOT EXISTS"
                            )
                            await result.consume()
                            logger.info(f"{database} created")
                            connected = True
                    except (neo4jExceptions.ClientError, neo4jExceptions.DatabaseError) as e:
                        if (e.code == "Neo.ClientError.Statement.UnsupportedAdministrationCommand") or \
                           (e.code == "Neo.DatabaseError.Statement.ExecutionFailed"):
                            if database is not None:
                                logger.warning(
                                    "This Neo4j instance does not support creating databases. "
                                    "Try to use Neo4j Desktop/Enterprise version or DozerDB instead. "
                                    "Fallback to use the default database."
                                )
                            if database is None:
                                logger.error(f"Failed to create {database}")
                                raise e
            
            if connected:
                # Create index for base nodes on entity_id if it doesn't exist
                try:
                    await cls._create_indexes(driver, database)
                except Exception as e:
                    logger.warning(f"Failed to create index: {str(e)}")
                return database
        
        raise RuntimeError("Failed to connect to any database")

    @classmethod
    async def _create_indexes(cls, driver: AsyncDriver, database: str):
        """Create necessary indexes"""
        async with driver.session(database=database) as session:
            # Check if index exists first
            check_query = """
            CALL db.indexes() YIELD name, labelsOrTypes, properties
            WHERE labelsOrTypes = ['base'] AND properties = ['entity_id']
            RETURN count(*) > 0 AS exists
            """
            try:
                check_result = await session.run(check_query)
                record = await check_result.single()
                await check_result.consume()

                index_exists = record and record.get("exists", False)

                if not index_exists:
                    result = await session.run(
                        "CREATE INDEX FOR (n:base) ON (n.entity_id)"
                    )
                    await result.consume()
                    logger.info(f"Created index for base nodes on entity_id in {database}")
            except Exception:
                # Fallback if db.indexes() is not supported
                result = await session.run(
                    "CREATE INDEX IF NOT EXISTS FOR (n:base) ON (n.entity_id)"
                )
                await result.consume()
```

### 2. 改造 Neo4JStorage 使用全局 Driver ✓

已完全重构 `aperag/graph/lightrag/kg/neo4j_impl.py`：

1. **导入全局管理器**：添加了对 `neo4j_manager` 的导入
2. **完全重写 initialize() 方法**：
   - 移除所有 fallback 逻辑
   - 只从全局管理器获取 driver  
   - 使用全局管理器的数据库准备功能
   - 移除本地配置读取、数据库创建、索引创建逻辑
3. **简化 finalize() 方法**：只清理引用，不关闭全局 driver

```python
async def initialize(self):
    # Get global Neo4j driver instance (no fallback)
    if neo4j_manager is None:
        raise RuntimeError("Global Neo4j manager is not available")
    
    self._driver = await neo4j_manager.get_driver()
    
    # Prepare database and get database name
    self._DATABASE = await neo4j_manager.prepare_neo4j_database(self.workspace)

async def finalize(self):
    """Clean up resources - driver is managed globally, so nothing to do"""
    self._driver = None
```

### 3. 优化事件循环清理逻辑 ✓

已修改 `aperag/graph/stateless_task_wrapper.py` 的清理逻辑，使用超时和主动取消，避免无限等待：

```python
finally:
    # Clean up event loop without waiting for background tasks
    try:
        # Cancel all pending tasks first
        pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
        if pending:
            logger.info(f"Cancelling {len(pending)} pending tasks during cleanup")
            for task in pending:
                task.cancel()
            
            # Wait briefly for cancellation to take effect
            try:
                loop.run_until_complete(asyncio.wait(pending, timeout=1.0))
            except Exception as e:
                logger.debug(f"Some tasks didn't cancel cleanly: {e}")
    except Exception as e:
        logger.debug(f"Exception during task cleanup: {e}")
    finally:
        loop.close()
        asyncio.set_event_loop(None)
```