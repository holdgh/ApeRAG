# LightRAG 无状态化改造方案

## 核心理念

将LightRAG从一个有状态的文档管理系统改造为**无状态的图索引构建服务**。每次调用都是独立的，不依赖任何全局状态或实例状态。

## 现状问题

1. **全局状态污染**：`shared_storage.py` 的全局变量导致并发冲突
2. **文档管理复杂**：内置的文档扫描、状态管理增加了不必要的复杂度
3. **接口过于综合**：`ainsert` 混合了文档管理、分块、实体抽取等多个职责
4. **并发限制**：`pipeline_status["busy"]` 全局锁导致无法真正并发

## 已实施的改造方案

### 1. 接口拆分设计

已将现有的 `ainsert` 拆分为三个独立的无状态接口：

#### 1.1 ainsert_document
```python
async def ainsert_document(
    self,
    documents: List[str],
    doc_ids: List[str] | None = None,
    file_paths: List[str] | None = None,
) -> Dict[str, Any]:
    """
    纯粹的文档写入功能
    - 写入 full_docs
    - 写入 doc_status (状态设为PENDING)
    - 返回文档元数据
    """
    # 无状态实现，直接写入存储
    # 没有全局锁检查
    # 没有pipeline_status依赖
```

#### 1.2 aprocess_chunking
```python
async def aprocess_chunking(
    self,
    doc_id: str,
    content: str | None = None,
    file_path: str = "unknown_source",
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
) -> Dict[str, Any]:
    """
    纯粹的文档分块功能
    - 如果content为None，从full_docs读取
    - 执行分块算法
    - 写入 chunks_vdb 和 text_chunks
    - 更新 doc_status (状态设为PROCESSING)
    - 返回chunks数据
    """
    # 无状态实现，不依赖全局变量
```

#### 1.3 aprocess_graph_indexing
```python
async def aprocess_graph_indexing(
    self,
    chunks: Dict[str, Any],
    collection_id: str | None = None,
) -> Dict[str, Any]:
    """
    核心图索引构建功能
    - 实体和关系抽取（extract_entities）
    - 合并和存储（merge_nodes_and_edges）
    - 写入 entities_vdb, relationships_vdb
    - 写入 chunk_entity_relation_graph
    """
    # 无 pipeline_status
    # 无全局锁（只有merge_nodes_and_edges内部的graph_db_lock）
```

### 2. 辅助方法

#### 2.1 获取Chunks数据
```python
async def aget_chunks_by_doc_id(self, doc_id: str) -> Dict[str, Any]:
    """获取文档的所有chunks"""
    
async def aget_chunks_by_ids(self, chunk_ids: List[str]) -> Dict[str, Any]:
    """根据ID列表获取特定chunks"""
```

### 3. Celery集成方案

#### 3.1 基础任务类
```python
class LightRAGStatelessTask(Task):
    """
    无状态任务基类
    - 每个worker进程维护LightRAG实例缓存
    - 独立的事件循环管理
    - 避免与Celery事件循环冲突
    """
    _instances: Dict[str, LightRAG] = {}
    
    def run_async(self, coro):
        """在新的事件循环中运行异步任务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)
```

#### 3.2 无状态任务实现
```python
@app.task(base=LightRAGStatelessTask, bind=True)
def insert_documents(self, documents, collection_id, doc_ids=None, file_paths=None):
    """文档插入任务"""

@app.task(base=LightRAGStatelessTask, bind=True)
def process_document_chunking(self, doc_id, content, collection_id, file_path):
    """文档分块任务"""

@app.task(base=LightRAGStatelessTask, bind=True)
def extract_graph_index(self, chunks, collection_id):
    """图索引构建任务"""

@app.task(base=LightRAGStatelessTask, bind=True)
def get_document_chunks(self, doc_id, collection_id):
    """获取chunks任务"""
```

### 4. 工作流示例

```python
@app.task
def process_document_workflow(document, collection_id, doc_id=None, file_path="unknown"):
    """
    完整的文档处理工作流
    1. 插入文档
    2. 文档分块  
    3. 抽取实体和关系
    """
    # Step 1: 插入文档
    insert_result = insert_documents.apply_async(
        args=[[document], collection_id],
        kwargs={"doc_ids": [doc_id], "file_paths": [file_path]}
    ).get()
    
    # Step 2: 分块
    chunk_result = process_document_chunking.apply_async(
        args=[doc_id, document, collection_id],
        kwargs={"file_path": file_path}
    ).get()
    
    # Step 3: 图索引
    chunks = chunk_result.get("chunks_data")
    graph_result = extract_graph_index.apply_async(
        args=[chunks, collection_id]
    ).get()
    
    return {
        "doc_id": doc_id,
        "chunks_created": chunk_result["chunk_count"],
        "entities_extracted": graph_result["entities_extracted"],
        "relations_extracted": graph_result["relations_extracted"],
    }
```

## 改造优势

### 1. 真正的并发能力
- 不同collection可以真正并发处理
- 没有全局`pipeline_status["busy"]`限制
- 每个任务独立执行

### 2. 灵活的组合
- 可以单独调用任何一个接口
- 可以跳过某些步骤（如直接处理已有的chunks）
- 易于构建自定义工作流

### 3. 更好的错误处理
- 任务级别的错误隔离
- 可以重试单个失败的步骤
- 不会影响其他正在处理的文档

### 4. 与Celery完美集成
- 独立的事件循环管理
- 避免了事件循环冲突
- 支持真正的分布式处理

## 使用建议

### 1. 批量处理
```python
# 并行处理多个文档
@app.task
def batch_process_documents(documents, collection_id):
    jobs = []
    for doc in documents:
        job = process_document_workflow.apply_async(
            args=[doc["content"], collection_id],
            kwargs={"doc_id": doc.get("doc_id")}
        )
        jobs.append(job)
    
    # 收集结果
    results = [job.get() for job in jobs]
    return results
```

### 2. 增量处理
```python
# 只处理新的chunks
new_chunks = get_new_chunks_from_somewhere()
result = extract_graph_index.delay(new_chunks, collection_id)
```

### 3. 错误重试
```python
# 使用Celery的重试机制
@app.task(bind=True, max_retries=3)
def resilient_graph_indexing(self, chunks, collection_id):
    try:
        return extract_graph_index(chunks, collection_id)
    except Exception as exc:
        # 指数退避重试
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

## 注意事项

1. **存储依赖**：虽然接口无状态，但仍依赖底层存储（PostgreSQL、Neo4j等）
2. **实例缓存**：每个worker进程会缓存LightRAG实例，需要考虑内存使用
3. **事务性**：需要在应用层处理事务一致性
4. **并发限制**：`merge_nodes_and_edges`内部仍有`graph_db_lock`，但这是必要的数据一致性保护

## 未来改进方向

1. **完全移除全局锁**：将`graph_db_lock`改为更细粒度的锁
2. **流式处理**：支持流式处理大文档
3. **更细粒度的接口**：如单独的实体抽取、关系抽取接口
4. **原生异步Celery**：当Celery支持原生异步时，可以简化事件循环管理

## 代码示例

### 无状态的 aprocess_graph_indexing 实现
```python
async def aprocess_graph_indexing(
    self,
    chunks: List[Dict[str, Any]],
    collection_id: str,
) -> Dict[str, Any]:
    """无状态的图索引构建"""
    
    # 1. 实体和关系抽取（核心算法）
    chunk_results = await extract_entities(
        chunks,
        global_config=asdict(self),
        # 不传递 pipeline_status 相关参数
    )
    
    # 2. 合并实体和关系
    await merge_nodes_and_edges(
        chunk_results=chunk_results,
        knowledge_graph_inst=self.chunk_entity_relation_graph,
        entity_vdb=self.entities_vdb,
        relationships_vdb=self.relationships_vdb,
        global_config=asdict(self),
        # 不传递 pipeline_status 相关参数
    )
    
    # 3. 返回处理结果
    return {
        "status": "success",
        "collection_id": collection_id,
        "chunks_processed": len(chunks),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Celery 任务示例
```python
from celery import Celery
from aperag.graph.lightrag import LightRAG

app = Celery('lightrag_tasks', broker='redis://localhost:6379')

@app.task
async def build_graph_index(
    chunks: List[Dict[str, Any]],
    collection_id: str,
    working_dir: str
) -> Dict[str, Any]:
    """构建图索引的 Celery 任务"""
    
    # 创建无状态的 LightRAG 实例
    rag = LightRAG(
        working_dir=working_dir,
        workspace=collection_id,
        # 关闭自动状态管理
        auto_manage_storages_states=False
    )
    
    # 同步初始化存储
    await rag.initialize_storages()
    
    # 执行图索引构建
    result = await rag.aprocess_graph_indexing(chunks, collection_id)
    
    # 清理资源
    await rag.finalize_storages()
    
    return result
```

## 总结

无状态化改造将 LightRAG 从一个复杂的文档管理系统转变为专注的图索引构建服务。这种设计更适合在分布式环境中使用，能够充分利用 Celery 等任务队列的并发能力，实现真正的水平扩展。 