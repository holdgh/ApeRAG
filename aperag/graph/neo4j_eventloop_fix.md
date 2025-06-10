# Neo4j 事件循环冲突修复记录

## 问题描述

在运行 Celery 任务时遇到以下错误：

```
Task <Task pending name='Task-161' coro=<StreamReader.read() running at /Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/streams.py:711> cb=[_release_waiter(<Future pendi...ask_wakeup()]>)() at /Users/earayu/Documents/GitHub/apecloud/ApeRAG/.venv/lib/python3.11/site-packages/neo4j/_async_compat/shims/__init__.py:38]> got Future <Future pending> attached to a different loop
```

## 根本原因分析

### 第一次重构的问题
我们最初从基于 PID 的全局状态管理改为依赖注入模式，但仍然存在事件循环冲突：

1. **WorkerConnectionPool 设计缺陷**：试图在 Worker 启动时创建连接，然后在不同的 Celery 任务事件循环中使用
2. **跨事件循环共享连接**：Neo4j 驱动在 worker_process_init 信号的事件循环中创建，但在 Celery 任务的事件循环中使用
3. **asyncio.Lock 冲突**：类级别的 `asyncio.Lock()` 在模块导入时创建，绑定到默认事件循环

### 事件循环隔离的重要性
- Celery 任务运行在独立的事件循环中
- Neo4j 驱动的异步操作（如连接、查询）必须在同一个事件循环中创建和使用
- 跨事件循环共享 asyncio 对象（Task、Future、Lock 等）会导致 "attached to a different loop" 错误

## 最终解决方案：事件循环感知的全局连接池

### 架构演进

#### 第一阶段：事件循环安全的连接工厂
```python
class Neo4jConnectionFactory:
    """每个任务创建独立连接，避免事件循环冲突"""
    
    @classmethod
    async def get_connection_manager(cls) -> Neo4jConnectionManager:
        # 在当前事件循环中创建新的连接管理器
        manager = Neo4jConnectionManager(cls._config)
        return manager
```

**问题**：虽然解决了事件循环冲突，但每个任务都创建和销毁连接，性能损耗较大。

#### 第二阶段：事件循环感知的全局连接池
```python
class GlobalNeo4jConnectionPool:
    """为每个事件循环维护独立的连接池"""
    
    async def get_pool(self) -> EventLoopConnectionPool:
        loop_id = self._get_loop_id()  # 获取当前事件循环ID
        # 为每个事件循环创建独立的连接池
        if loop_id not in self._pools:
            self._pools[loop_id] = EventLoopConnectionPool(config, loop_id)
        return self._pools[loop_id]
```

### 核心设计原则

#### 1. 事件循环隔离
- **每个事件循环有独立的连接池**
- **连接在同一事件循环内创建、使用、复用**
- **使用事件循环ID作为池标识**

#### 2. 连接借用模式
```python
class BorrowedConnection:
    """安全的连接借用和归还机制"""
    
    async def __aenter__(self) -> 'BorrowedConnection':
        self.connection = await self.pool_manager.borrow_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.pool_manager.return_connection(self.connection)
```

#### 3. 生命周期管理
- **借用**：任务开始时从池中借用连接
- **使用**：在任务期间独占使用连接
- **归还**：任务完成后归还到池中
- **复用**：下个任务可以复用已有连接

### 新架构组件

#### GlobalNeo4jConnectionPool
```python
# 全局连接池管理器
pool = GlobalNeo4jConnectionPool()
- 管理多个事件循环的连接池
- 自动检测事件循环并创建对应的池
- 使用弱引用追踪事件循环生命周期
```

#### EventLoopConnectionPool  
```python
# 单个事件循环的连接池
loop_pool = EventLoopConnectionPool(config, loop_id)
- 维护可用连接列表 (available_connections)
- 追踪使用中连接集合 (in_use_connections)
- 支持连接借用/归还操作
- 配置最大/最小连接数
```

#### PooledConnectionManager
```python
# 池化的连接管理器
connection = PooledConnectionManager(config, pool)
- 封装 Neo4j 驱动实例
- 支持数据库准备和缓存
- 标记使用状态 (in_use/available)
- 提供连接健康检查
```

#### BorrowedConnection
```python
# 连接借用上下文管理器
async with Neo4jConnectionFactory.borrow_connection() as borrowed:
    driver = await borrowed.get_driver()
    database = await borrowed.prepare_database(workspace)
    # 使用连接进行数据库操作
# 自动归还连接到池
```

### 实现细节

#### 事件循环ID生成
```python
def _get_loop_id(self) -> str:
    """使用事件循环对象ID作为唯一标识"""
    loop = asyncio.get_running_loop()
    return f"{id(loop)}"
```

#### 连接池统计
```python
# 实时监控连接池状态
stats = await Neo4jConnectionFactory.get_pool_stats()
# 输出：{
#   "140234567890": {  # 事件循环ID
#     "available": 3,
#     "in_use": 2, 
#     "total": 5,
#     "max_size": 10
#   }
# }
```

#### 数据库准备缓存
```python
class BorrowedConnection:
    def __init__(self):
        self._database_cache: Dict[str, str] = {}
    
    async def prepare_database(self, workspace: str) -> str:
        # 缓存数据库准备结果，避免重复操作
        if workspace in self._database_cache:
            return self._database_cache[workspace]
        # ...
```

### Storage 使用方式

#### 简化的初始化
```python
async def initialize(self):
    # 借用连接
    self._borrowed_connection = Neo4jConnectionFactory.borrow_connection()
    await self._borrowed_connection.__aenter__()
    
    # 获取驱动和数据库
    self._driver = await self._borrowed_connection.get_driver()
    self._DATABASE = await self._borrowed_connection.prepare_database(self.workspace)
```

#### 自动清理
```python
async def finalize(self):
    # 归还连接到池
    if self._borrowed_connection:
        await self._borrowed_connection.__aexit__(None, None, None)
        self._borrowed_connection = None
```

## 性能优势

### 1. 连接复用
- ✅ **同事件循环内连接复用**：避免重复创建 TCP 连接
- ✅ **数据库准备缓存**：避免重复数据库创建和索引操作
- ✅ **连接池管理**：自动维护最优连接数量

### 2. 内存效率
- ✅ **按需创建**：只在有任务时创建连接
- ✅ **自动回收**：事件循环结束时自动清理池
- ✅ **弱引用追踪**：防止内存泄漏

### 3. 并发性能
- ✅ **真正的并发**：多个事件循环可并行工作
- ✅ **无全局锁**：每个池独立管理，无竞争
- ✅ **事件循环安全**：完全避免跨循环冲突

## 配置选项

### 连接池配置
```python
config = Neo4jConnectionConfig(
    # Neo4j 连接设置
    uri="neo4j://localhost:7687",
    username="neo4j",
    password="password",
    max_connection_pool_size=50,  # Neo4j 驱动内部连接池
    
    # 应用层连接池设置
    pool_max_size=10,  # 每个事件循环最大连接数
    pool_min_size=2,   # 每个事件循环最小连接数
)
```

### 监控和调试
```python
# 获取连接池统计
stats = await Neo4jConnectionFactory.get_pool_stats()
print(f"活跃事件循环数: {len(stats)}")
for loop_id, pool_stats in stats.items():
    print(f"循环 {loop_id}: {pool_stats}")

# 输出示例：
# 活跃事件循环数: 2
# 循环 140234567890: {'available': 3, 'in_use': 2, 'total': 5, 'max_size': 10}
# 循环 140234567891: {'available': 1, 'in_use': 0, 'total': 1, 'max_size': 10}
```

## Worker 生命周期管理

### 启动阶段
```python
def setup_worker_neo4j_config(**kwargs):
    # 初始化全局配置
    config = Neo4jConnectionConfig()
    GlobalNeo4jConnectionPool.set_config(config)
    # 注意：不创建连接，只设置配置
```

### 运行阶段
```python
# 每个 Celery 任务
async def lightrag_task():
    # 任务开始：从池中借用连接
    async with Neo4jConnectionFactory.borrow_connection() as conn:
        driver = await conn.get_driver()
        # 使用连接进行操作
    # 任务结束：自动归还连接到池
```

### 关闭阶段
```python
async def cleanup_worker_neo4j_config_async(**kwargs):
    # 关闭所有事件循环的连接池
    pool = GlobalNeo4jConnectionPool()
    await pool.close_all_pools()
```

## 关键经验总结

### 1. 事件循环隔离原则
- **核心原则**：asyncio 对象必须在同一事件循环中创建和使用
- **实现方式**：为每个事件循环维护独立的资源池
- **好处**：彻底避免跨循环冲突，支持真正的并发

### 2. 连接池设计模式
- **分层设计**：全局管理器 → 事件循环池 → 具体连接
- **借用模式**：使用上下文管理器确保资源安全归还
- **生命周期**：连接在池中复用，池随事件循环管理

### 3. 性能优化策略
- **配置共享**：Worker 级别共享配置，避免重复解析
- **连接复用**：事件循环级别复用连接，减少创建开销
- **数据库缓存**：缓存数据库准备结果，避免重复操作

## 测试验证

### 功能测试
```python
# 测试连接借用和归还
async def test_connection_pool():
    # 借用连接
    async with Neo4jConnectionFactory.borrow_connection() as conn:
        driver = await conn.get_driver()
        # 验证连接可用
        await driver.verify_connectivity()
    
    # 验证连接已归还
    stats = await Neo4jConnectionFactory.get_pool_stats()
    assert stats[loop_id]["in_use"] == 0
```

### 性能测试
```python
# 测试连接复用
async def test_connection_reuse():
    # 第一次任务
    async with Neo4jConnectionFactory.borrow_connection() as conn1:
        driver1 = await conn1.get_driver()
        driver1_id = id(driver1)
    
    # 第二次任务
    async with Neo4jConnectionFactory.borrow_connection() as conn2:
        driver2 = await conn2.get_driver()
        driver2_id = id(driver2)
    
    # 验证连接被复用
    assert driver1_id == driver2_id
```

### 并发测试
```python
# 测试并发安全性
async def test_concurrent_tasks():
    tasks = []
    for i in range(10):
        task = asyncio.create_task(process_document(f"doc_{i}"))
        tasks.append(task)
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks)
    
    # 验证无冲突，所有任务成功
    assert all(result["status"] == "success" for result in results)
```

## 总结

这个**事件循环感知的全局连接池**架构完美解决了 Neo4j 在 Celery 环境中的问题：

- 🎯 **彻底解决事件循环冲突**：每个循环独立池，无跨循环共享
- 🚀 **实现高效连接复用**：同循环内任务复用连接，减少开销  
- 🔧 **提供清晰的资源管理**：借用/归还模式，自动生命周期管理
- 🧪 **确保并发安全**：多循环并行工作，无锁竞争
- 📦 **保持向后兼容**：Storage API 无需修改，透明升级

这个解决方案既满足了用户对连接复用的性能需求，又解决了 Celery 多任务环境下的事件循环冲突问题，为 ApeRAG 提供了一个健壮、高效的 Neo4j 连接管理解决方案。 