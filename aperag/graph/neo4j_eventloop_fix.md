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

## 解决方案：事件循环安全的连接工厂

### 新架构特点

#### 1. Neo4jConnectionFactory 模式
```python
class Neo4jConnectionFactory:
    """
    事件循环安全的连接工厂
    - 共享配置，独立连接
    - 每个任务在自己的事件循环中创建连接
    """
    _config: Optional[Neo4jConnectionConfig] = None
    
    @classmethod
    async def get_connection_manager(cls) -> Neo4jConnectionManager:
        # 在当前事件循环中创建新的连接管理器
        manager = Neo4jConnectionManager(cls._config)
        return manager
```

#### 2. 配置共享，连接隔离
- **配置层面**：Worker 启动时初始化共享配置（环境变量解析）
- **连接层面**：每个任务创建独立的连接管理器和驱动实例
- **生命周期**：每个 storage 实例管理自己的连接生命周期

#### 3. 线程安全的配置管理
```python
# 使用线程锁而非 asyncio.Lock 避免事件循环依赖
import threading
if not hasattr(cls, '_thread_lock'):
    cls._thread_lock = threading.Lock()

with cls._thread_lock:
    if cls._config is None:
        cls._config = Neo4jConnectionConfig()
```

### 实现细节

#### Worker 信号处理简化
```python
# 之前：尝试跨事件循环共享连接（错误）
async def setup_worker_connections(**kwargs):
    pool = WorkerConnectionPool()
    await pool.get_connection_manager()  # 绑定到信号事件循环

# 现在：只初始化配置（正确）
def setup_worker_neo4j_config(**kwargs):
    config = Neo4jConnectionConfig()
    Neo4jConnectionFactory._config = config  # 共享配置，不共享连接
```

#### Storage 初始化策略
```python
async def initialize(self):
    # 在当前任务的事件循环中创建连接管理器
    if Neo4jConnectionFactory is not None:
        self._connection_manager = await Neo4jConnectionFactory.get_connection_manager()
    else:
        self._connection_manager = Neo4jConnectionManager()
    
    # 驱动在同一事件循环中创建和使用
    self._driver = await self._connection_manager.get_driver()
```

#### 资源清理策略
```python
async def finalize(self):
    # 每个 storage 实例负责清理自己的连接
    if self._connection_manager:
        await self._connection_manager.close()
        self._connection_manager = None
```

## 修复效果

### 解决的问题
1. ✅ **事件循环冲突**：每个任务在自己的事件循环中操作连接
2. ✅ **连接复用优化**：通过共享配置减少重复初始化开销  
3. ✅ **资源管理清晰**：明确的连接生命周期和清理策略
4. ✅ **向后兼容**：Neo4jStorage API 保持不变

### 性能优势
- **配置复用**：Worker 级别的配置共享，避免重复环境变量解析
- **连接优化**：每个连接使用 Neo4j 的内置连接池优化
- **内存管理**：任务完成后自动清理连接，避免内存泄漏
- **并发安全**：真正的并发任务处理，无全局锁瓶颈

## 关键经验

### 1. 事件循环隔离原则
- **永远不要跨事件循环共享 asyncio 对象**
- **在需要的地方创建，在同一地方使用**
- **优先考虑配置共享而非连接共享**

### 2. Celery 异步任务最佳实践
- 每个任务应该管理自己的异步资源
- 使用工厂模式创建资源，避免全局状态
- Worker 信号适合初始化配置，不适合创建连接

### 3. 连接管理策略
- **配置层面**：Worker 级别共享（减少解析开销）
- **连接层面**：任务级别隔离（避免冲突）  
- **清理层面**：实例级别管理（明确责任）

## 测试验证

### 修复前的错误模式
```python
# 错误：在不同事件循环中使用连接
worker_init_loop = asyncio.new_event_loop()  # Worker 启动
task_loop = asyncio.new_event_loop()         # Celery 任务
# driver 在 worker_init_loop 创建，在 task_loop 使用 → 冲突
```

### 修复后的正确模式  
```python
# 正确：在同一事件循环中创建和使用
task_loop = asyncio.get_running_loop()  # 当前任务事件循环
# driver 在 task_loop 创建，在 task_loop 使用 → 安全
```

### 验证指标
- ✅ 消除 "attached to a different loop" 错误
- ✅ LightRAG 任务正常完成图索引构建
- ✅ 多个并发任务无冲突
- ✅ 连接资源正确清理

## 总结

这次修复彻底解决了 Neo4j 连接管理的事件循环冲突问题。通过采用**事件循环安全的连接工厂模式**，我们实现了：

- 🎯 **架构清晰**：配置共享 + 连接隔离
- 🚀 **性能优化**：减少重复初始化开销
- 🔧 **易于维护**：明确的生命周期管理
- 🧪 **稳定可靠**：消除并发冲突
- 📦 **向后兼容**：现有代码无需修改

这个解决方案为 ApeRAG 在 Celery 环境中的稳定运行提供了坚实的基础。 