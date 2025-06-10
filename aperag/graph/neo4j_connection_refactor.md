# Neo4j 连接管理架构重构

## 概述

我们重构了 Neo4j 连接管理架构，从基于 PID 的全局状态管理改为**依赖注入 + AsyncContextManager**模式。这个新架构解决了之前的事件循环冲突、全局状态复杂性等问题。

## 核心改进

### 1. 摒弃全局状态
- ❌ **旧方案**: 使用模块级全局变量 `neo4j_manager` 和 PID 字典
- ✅ **新方案**: 每个组件管理自己的连接，通过依赖注入传递

### 2. 清晰的生命周期管理
- ❌ **旧方案**: 懒加载锁机制，生命周期不明确
- ✅ **新方案**: AsyncContextManager 明确资源创建和销毁时机

### 3. 更好的 Worker 支持
- ❌ **旧方案**: 使用 PID 作为连接标识符
- ✅ **新方案**: Worker 级别的连接池，与 Celery 生命周期信号集成

## 新架构组件

### Neo4jConnectionConfig
```python
# 连接配置管理
config = Neo4jConnectionConfig(
    uri="neo4j://localhost:7687",
    username="neo4j", 
    password="password123",
    max_connection_pool_size=50
)
```

### Neo4jConnectionManager
```python
# 单个连接管理器
async with Neo4jConnectionManager(config) as manager:
    driver = await manager.get_driver()
    # 使用 driver 进行数据库操作
# 连接自动关闭
```

### Neo4jConnectionFactory
```python
# 事件循环安全的连接工厂（Celery/Prefect）
factory = Neo4jConnectionFactory()
manager = await factory.get_connection_manager()
driver = await manager.get_driver()
```

## 使用场景

### 1. 在 Celery 任务中使用
```python
# Neo4jStorage 会自动从 Worker 连接池获取连接
storage = Neo4JStorage(namespace="entities", workspace="collection_123", ...)
await storage.initialize()  # 自动使用 worker 级别的连接
```

### 2. 在独立脚本中使用
```python
# 创建独立的连接管理器
async with Neo4jConnectionManager() as manager:
    driver = await manager.get_driver()
    # 使用 driver
# 连接自动关闭
```

### 3. 在测试中使用
```python
# 轻松模拟数据库连接
mock_config = Neo4jConnectionConfig(uri="neo4j://test:7687")
async with Neo4jConnectionManager(mock_config) as manager:
    # 测试逻辑
```

## Worker 生命周期管理

### Celery 集成
```python
# config/celery.py 中自动配置
from celery.signals import worker_process_init, worker_process_shutdown
from aperag.db.neo4j_manager import setup_worker_neo4j_config, cleanup_worker_neo4j_config

worker_process_init.connect(setup_worker_neo4j_config)
worker_process_shutdown.connect(cleanup_worker_neo4j_config)
```

### Worker 启动流程
1. Worker 进程启动
2. `worker_process_init` 信号触发
3. `Neo4jConnectionFactory` 初始化共享配置
4. 每个任务在自己的事件循环中创建独立连接

### Worker 关闭流程
1. Worker 进程关闭
2. `worker_process_shutdown` 信号触发  
3. `Neo4jConnectionFactory` 清理共享配置
4. 各任务的连接自动清理

## 迁移指南

### 代码变更最小
大部分代码**无需修改**：
- `Neo4jStorage` 的 API 保持不变
- 现有的 `initialize()` 和 `finalize()` 方法正常工作
- 所有数据库操作方法保持兼容

### 环境变量保持不变
```bash
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123
NEO4J_MAX_CONNECTION_POOL_SIZE=50
```

### Celery 配置自动生效
- 修改后的 `config/celery.py` 自动启用新的连接管理
- Worker 启动时自动初始化连接池
- 无需手动配置

## 性能优势

### 1. 消除全局锁竞争
- 移除 `_get_lock()` 懒加载锁机制
- 每个连接管理器独立工作
- 避免跨组件的锁竞争

### 2. 更好的连接复用
- Worker 级别的连接共享
- 避免每个任务创建新连接的开销
- TCP 连接保持在 Worker 生命周期内

### 3. 更快的故障恢复
- 连接失败只影响单个管理器
- 不会影响其他组件的连接
- 明确的错误边界

## 故障排除

### 连接问题诊断
```python
# 检查连接状态
manager = Neo4jConnectionManager()
try:
    driver = await manager.get_driver()
    print("Neo4j connection successful")
except Exception as e:
    print(f"Neo4j connection failed: {e}")
```

### Worker 连接问题
```python
# 检查 Worker 连接工厂
factory = Neo4jConnectionFactory()
manager = await factory.get_connection_manager()
print(f"Worker {os.getpid()}: Connection manager ready")
```

### 日志监控
```
INFO  Worker 12345: Neo4j configuration initialized
INFO  Neo4jStorage using event-loop-safe connection factory for workspace 'collection_123'
INFO  Neo4j driver initialized successfully
```

## 最佳实践

### 1. 在长期服务中
```python
# 推荐：使用 AsyncContextManager
async with Neo4jConnectionManager() as manager:
    # 长期运行的服务逻辑
    pass
```

### 2. 在 Celery 任务中  
```python
# 推荐：直接使用 Neo4jStorage，自动创建事件循环安全的连接
@app.task
def process_document(collection_id):
    storage = Neo4JStorage(workspace=collection_id, ...)
    await storage.initialize()  # 在当前事件循环中创建连接
```

### 3. 在测试中
```python
# 推荐：使用测试专用配置
test_config = Neo4jConnectionConfig(uri="neo4j://test:7687")
async with Neo4jConnectionManager(test_config) as manager:
    # 测试逻辑，不影响生产环境
```

## 总结

新的 Neo4j 连接管理架构提供了：

- 🎯 **更清晰的架构**：依赖注入替代全局状态
- 🚀 **更好的性能**：消除全局锁竞争
- 🔧 **更易维护**：明确的生命周期管理
- 🧪 **更好的测试性**：轻松模拟和隔离
- 📦 **无缝迁移**：现有代码基本无需修改

这个重构彻底解决了之前 PID 方案的问题，为 ApeRAG 提供了一个健壮、可扩展的 Neo4j 连接管理解决方案。 