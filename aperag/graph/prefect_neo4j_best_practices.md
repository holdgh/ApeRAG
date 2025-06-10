# Prefect + Neo4j异步最佳实践

## 核心理念

你的理解非常准确：在Prefect等异步任务队列中，一个Worker进程会有多个长生命周期的事件循环，Neo4j连接池与事件循环是1:N的关系。

## 设计原则

### 1. 每个事件循环独立的驱动实例
```python
# ✅ 正确：每个事件循环有自己的驱动
loop1 -> driver1 (内置连接池)
loop2 -> driver2 (内置连接池)
loop3 -> driver3 (内置连接池)

# ❌ 错误：跨事件循环共享驱动
driver -> loop1, loop2, loop3  # 会导致连接错误
```

### 2. 自动生命周期管理
- 使用弱引用自动跟踪事件循环
- 当事件循环被垃圾回收时，自动清理对应的驱动
- 无需手动管理驱动的创建和销毁

### 3. 线程安全的注册表
- Prefect可能在多个线程中创建事件循环
- 使用线程锁保护驱动注册表的并发访问

## 实现细节

### EventLoopDriverRegistry
```python
class EventLoopDriverRegistry:
    def __init__(self):
        # 弱引用字典：事件循环 -> 驱动
        self._drivers: weakref.WeakKeyDictionary[
            asyncio.AbstractEventLoop, 
            AsyncGraphDatabase.driver
        ] = weakref.WeakKeyDictionary()
```

**关键特性**：
- 使用`WeakKeyDictionary`避免内存泄漏
- 当事件循环被垃圾回收时，对应的驱动自动从字典中移除
- 使用`weakref.finalize`注册清理回调

### ContextVar优化
```python
_driver_context: ContextVar[Optional['AsyncGraphDatabase.driver']] = ContextVar(
    'neo4j_async_driver', 
    default=None
)
```

**优势**：
- 在同一个异步上下文中缓存驱动
- 避免重复查找
- 支持嵌套的异步调用

## 使用模式

### 1. 基础使用
```python
@task
async def my_task(data: dict):
    # 自动获取当前事件循环的驱动
    results = await Neo4jAsyncConnectionManager.execute_query(
        "MATCH (n:Node {id: $id}) RETURN n",
        {"id": data["id"]}
    )
    return results
```

### 2. Session装饰器模式
```python
@task
@with_neo4j_session()
async def batch_operation(session, items: list):
    # session自动注入，支持事务
    async with session.begin_transaction() as tx:
        for item in items:
            await tx.run("CREATE (n:Item) SET n = $props", props=item)
```

### 3. 并发任务
```python
@flow
async def parallel_processing():
    # Prefect会在不同的事件循环中运行这些任务
    # 每个任务都会获得正确的驱动实例
    results = await asyncio.gather(*[
        process_node.submit(node_id) 
        for node_id in node_ids
    ])
```

## 与Celery的对比

| 特性 | Celery（当前） | Prefect（未来） |
|-----|--------------|----------------|
| 任务模型 | 同步为主 | 原生异步支持 |
| 事件循环 | 每个任务创建新的 | Worker进程中多个长生命周期循环 |
| 驱动管理 | Worker级别单例 | 事件循环级别实例 |
| 连接复用 | Worker内复用 | 事件循环内复用 |
| 性能 | 需要同步驱动 | 充分利用异步性能 |

## 性能优化

### 1. 连接池配置
```python
NEO4J_MAX_POOL_SIZE=50  # 每个事件循环的最大连接数
NEO4J_CONN_TIMEOUT=60.0  # 获取连接超时
```

### 2. 监控指标
```python
async def monitor_connections():
    stats = await Neo4jAsyncConnectionManager.get_stats()
    # {
    #     'active_event_loops': 3,
    #     'event_loop_ids': [140234567, 140234568, 140234569]
    # }
```

### 3. 错误处理
```python
@task(retries=3, retry_delay_seconds=5)
async def resilient_task():
    try:
        return await Neo4jAsyncConnectionManager.execute_query(query)
    except ServiceUnavailable:
        # Neo4j暂时不可用，Prefect会自动重试
        raise
```

## LightRAG集成

### 异步适配器
```python
class LightRAGAsyncNeo4jAdapter:
    async def query(self, cypher: str, params: dict = None):
        # 直接使用异步连接管理器
        return await Neo4jAsyncConnectionManager.execute_query(
            cypher, params
        )
```

### 在Prefect任务中使用LightRAG
```python
@task
async def process_with_lightrag(document: str):
    adapter = LightRAGAsyncNeo4jAdapter()
    lightrag = LightRAG(
        graph_storage=adapter,
        # 其他配置...
    )
    
    # LightRAG操作
    await lightrag.ainsert(document)
    results = await lightrag.aquery("查询内容")
    return results
```

## 最佳实践总结

1. **不要跨事件循环共享连接**
   - 每个事件循环都应该有自己的驱动实例
   - 使用提供的连接管理器自动处理

2. **利用Prefect的并发能力**
   - 使用`asyncio.gather`并发执行多个任务
   - 每个任务会在合适的事件循环中获得正确的连接

3. **监控和调试**
   - 定期记录连接统计信息
   - 使用Prefect的重试机制处理瞬时故障

4. **优雅关闭**
   - 在应用关闭时调用`close_all()`
   - 或依赖自动清理机制

## 迁移建议

从Celery迁移到Prefect时：

1. **保留同步实现**作为备份
2. **逐步迁移**任务到异步版本
3. **测试并发场景**确保连接管理正确
4. **监控性能**对比同步和异步的表现

这个设计充分利用了Neo4j驱动的内置连接池，同时正确处理了异步环境中的事件循环隔离问题。 