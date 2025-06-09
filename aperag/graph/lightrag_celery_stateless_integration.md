# LightRAG Celery 无状态集成改造

## 改造概述

本次改造将 Celery 任务中的 LightRAG 集成从使用 `ainsert` 改为使用新的无状态接口，解决了事件循环冲突和并发问题。

## 主要改动

### 1. 新增文件

#### `aperag/graph/lightrag/stateless_task_wrapper.py`

提供了一个专门用于 Celery 任务的包装器，主要特性：

- **StatelessLightRAGWrapper 类**：
  - 管理 LightRAG 实例的生命周期
  - 提供异步和同步方法
  - 处理事件循环管理，避免与 Celery 冲突

- **便捷函数**：
  - `process_document_for_celery()`: 处理文档的完整流程
  - `delete_document_for_celery()`: 删除文档

### 2. 修改的文件

#### `aperag/tasks/index.py`

**修改的函数**：

1. **`add_lightrag_index_task`**：
   - 移除了 `async_to_sync` 和内部异步函数
   - 使用 `process_document_for_celery` 替代 `ainsert`
   - 返回详细的处理结果（chunks数量、实体数量、关系数量）

2. **`remove_lightrag_index_task`**：
   - 简化了实现，移除异步代码
   - 使用 `delete_document_for_celery` 替代 `adelete_by_doc_id`
   - 改进错误处理

## 工作流程

### 文档处理流程

```python
# 1. 插入文档
insert_result = await rag.ainsert_document(
    documents=[content],
    doc_ids=[doc_id],
    file_paths=[file_path]
)

# 2. 处理分块
chunk_result = await rag.aprocess_chunking(
    doc_id=str(doc_id),
    content=content,
    file_path=file_path
)

# 3. 构建图索引
graph_result = await rag.aprocess_graph_indexing(
    chunks=chunks_data,
    collection_id=str(collection_id)
)
```

### 事件循环管理

每个 Celery 任务创建独立的事件循环：

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(async_method())
    return result
finally:
    loop.close()
    asyncio.set_event_loop(None)
```

## 优势

1. **无事件循环冲突**：每个任务使用独立的事件循环
2. **更好的并发支持**：使用无状态接口，避免全局锁
3. **详细的处理结果**：返回chunks、实体、关系的数量
4. **清晰的错误处理**：结构化的错误信息
5. **更简洁的代码**：移除了复杂的异步转同步逻辑

## 使用示例

### 在 Celery 任务中处理文档

```python
@app.task
def my_document_task(document_content, document_id, collection_id):
    collection = db_ops.query_collection_by_id(collection_id)
    
    result = process_document_for_celery(
        collection=collection,
        content=document_content,
        doc_id=str(document_id),
        file_path="example.txt"
    )
    
    if result["status"] == "success":
        print(f"Processed {result['chunks_created']} chunks")
        print(f"Extracted {result['entities_extracted']} entities")
        print(f"Found {result['relations_extracted']} relations")
```

### 直接使用包装器（在异步环境中）

```python
async def process_in_async_context():
    wrapper = StatelessLightRAGWrapper(collection, use_cache=True)
    result = await wrapper.process_document_async(
        content="Document content",
        doc_id="doc-123",
        file_path="test.txt"
    )
```

## 兼容性

- 保留了原有的 `lightrag_holder.py`，未做任何修改
- 新的接口与旧的 `ainsert` 功能等价，但更适合 Celery 环境
- 支持重试机制和错误恢复

## 注意事项

1. **不使用缓存**：Celery 任务默认 `use_cache=False`，避免跨任务状态共享
2. **文档ID转换**：确保文档ID转换为字符串格式
3. **错误重试**：保留了原有的重试配置

## 测试建议

1. 测试单个文档处理
2. 测试并发处理多个文档
3. 测试错误情况（如文档不存在、collection被删除）
4. 测试重试机制
5. 监控内存使用（确保事件循环正确清理） 