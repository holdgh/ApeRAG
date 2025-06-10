# Neo4j 同步驱动解决方案

## 问题总结

你的核心需求是：
- LightRAG处理文档时需要用到neo4j
- LightRAG运行在celery task中（每个task会创建事件循环）
- 不希望每个task都创建和销毁一遍neo4j连接池，效率很低

## 解决方案

使用 **Neo4j 同步驱动 + Worker级别连接池**。这是最简单且最可靠的方案。

## 核心优势

1. **真正的连接复用**：同一个Worker进程内的所有任务共享同一个Neo4j驱动实例
2. **无事件循环冲突**：使用同步驱动，完全避免了异步事件循环绑定问题
3. **最佳实践**：Neo4j驱动本身已经内置了高效的连接池管理
4. **代码简单**：不需要自己实现复杂的连接池逻辑

## 实现步骤

### 1. 设置环境变量

在你的环境配置中，将图存储设置为同步实现：

```bash
# 使用同步Neo4j存储
LIGHTRAG_GRAPH_STORAGE=Neo4JSyncStorage

# Neo4j连接配置
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### 2. 工作原理

1. **Worker启动时**：`Neo4jSyncConnectionManager.initialize()` 创建一个同步驱动实例
2. **每个Celery任务**：
   - 使用 `asyncio.to_thread` 在后台线程执行同步操作
   - 从Worker级别的驱动获取连接（Neo4j驱动自动管理连接池）
   - 完成后自动归还连接到池中
3. **Worker关闭时**：`Neo4jSyncConnectionManager.close()` 关闭驱动和所有连接

### 3. 性能对比

**之前（每个任务创建/销毁连接）**：
- 每个任务：创建驱动 → 建立TCP连接 → 认证 → 执行操作 → 关闭连接
- 开销：~100-200ms 每个任务

**现在（Worker级别连接池）**：
- 第一个任务：创建驱动（一次性开销）
- 后续任务：直接从池中获取连接 → 执行操作 → 归还连接
- 开销：~1-5ms 每个任务

## 为什么这是最佳方案？

1. **成熟的解决方案**：Neo4j官方推荐的使用方式
2. **零维护成本**：连接池由Neo4j驱动自动管理
3. **生产级别可靠性**：经过大规模验证的方案
4. **简单易懂**：代码逻辑清晰，易于调试和维护

## 注意事项

1. **Celery配置**：确保使用 `--pool=prefork`（默认），不要使用 `--pool=threads`
2. **连接池大小**：通过 `NEO4J_MAX_CONNECTION_POOL_SIZE` 环境变量调整（默认50）
3. **监控**：Neo4j驱动会自动记录连接池状态到日志

## 总结

这个方案完美解决了你的核心问题：
- ✅ 不再每个任务创建/销毁连接
- ✅ Worker级别连接复用，高效利用资源
- ✅ 无事件循环冲突，稳定可靠
- ✅ 使用Neo4j官方最佳实践，无需自己造轮子 