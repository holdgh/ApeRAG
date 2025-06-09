# LightRAG 无状态接口实现示例

## 拆分后的接口实现

### 1. ainsert_document - 文档写入接口

```python
async def ainsert_document(
    self,
    documents: List[str],
    doc_ids: Optional[List[str]] = None,
    file_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    纯粹的文档写入功能，无状态实现
    
    Args:
        documents: 文档内容列表
        doc_ids: 文档ID列表（可选）
        file_paths: 文件路径列表（可选）
    
    Returns:
        写入结果，包含文档ID映射
    """
    # 参数标准化
    if isinstance(documents, str):
        documents = [documents]
    
    if file_paths is None:
        file_paths = ["unknown_source"] * len(documents)
    elif isinstance(file_paths, str):
        file_paths = [file_paths]
    
    # 生成或验证文档ID
    if doc_ids is None:
        doc_ids = [
            compute_mdhash_id(clean_text(doc), prefix="doc-") 
            for doc in documents
        ]
    elif isinstance(doc_ids, str):
        doc_ids = [doc_ids]
    
    # 构建文档数据
    docs_to_store = {}
    status_to_store = {}
    
    for doc_id, content, file_path in zip(doc_ids, documents, file_paths):
        cleaned_content = clean_text(content)
        
        # 全文文档
        docs_to_store[doc_id] = {
            "content": cleaned_content,
            "file_path": file_path,
        }
        
        # 文档状态（兼容性）
        status_to_store[doc_id] = {
            "status": DocStatus.PENDING,
            "content": cleaned_content,
            "content_summary": get_content_summary(cleaned_content),
            "content_length": len(cleaned_content),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "file_path": file_path,
        }
    
    # 直接写入存储，无状态检查
    await asyncio.gather(
        self.full_docs.upsert(docs_to_store),
        self.doc_status.upsert(status_to_store)
    )
    
    return {
        "status": "success",
        "doc_ids": doc_ids,
        "count": len(doc_ids)
    }
```

### 2. aprocess_chunking - 文档分块接口

```python
async def aprocess_chunking(
    self,
    doc_id: str,
    content: str,
    file_path: str = "unknown_source",
    split_by_character: Optional[str] = None,
    split_by_character_only: bool = False,
) -> List[Dict[str, Any]]:
    """
    纯粹的文档分块功能，无状态实现
    
    Args:
        doc_id: 文档ID
        content: 文档内容
        file_path: 文件路径
        split_by_character: 分割字符
        split_by_character_only: 是否仅按字符分割
    
    Returns:
        分块列表
    """
    # 执行分块
    chunks = self.chunking_func(
        self.tokenizer,
        content,
        split_by_character,
        split_by_character_only,
        self.chunk_overlap_token_size,
        self.chunk_token_size,
    )
    
    # 构建分块数据
    chunks_data = {}
    chunks_list = []
    
    for idx, chunk_info in enumerate(chunks):
        chunk_id = compute_mdhash_id(chunk_info["content"], prefix="chunk-")
        
        chunk_data = {
            "content": chunk_info["content"],
            "tokens": chunk_info["tokens"],
            "chunk_order_index": idx,
            "full_doc_id": doc_id,
            "file_path": file_path,
        }
        
        chunks_data[chunk_id] = chunk_data
        chunks_list.append({
            "chunk_id": chunk_id,
            **chunk_data
        })
    
    # 写入存储（兼容性）
    await asyncio.gather(
        self.chunks_vdb.upsert(chunks_data),
        self.text_chunks.upsert(chunks_data)
    )
    
    return chunks_list
```

### 3. aprocess_graph_indexing - 核心图索引构建接口

```python
async def aprocess_graph_indexing(
    self,
    chunks: List[Dict[str, Any]],
    collection_id: str,
) -> Dict[str, Any]:
    """
    核心图索引构建功能，完全无状态
    
    Args:
        chunks: 分块数据列表，每个包含 chunk_id, content, file_path 等
        collection_id: 集合ID
    
    Returns:
        处理结果统计
    """
    # 准备分块数据格式
    chunks_dict = {
        chunk["chunk_id"]: {
            "content": chunk["content"],
            "tokens": chunk.get("tokens", 0),
            "chunk_order_index": chunk.get("chunk_order_index", 0),
            "full_doc_id": chunk.get("full_doc_id", ""),
            "file_path": chunk.get("file_path", "unknown_source"),
        }
        for chunk in chunks
    }
    
    # 1. 实体和关系抽取（无 pipeline_status）
    chunk_results = await extract_entities(
        chunks_dict,
        global_config=asdict(self),
        # 不传递 pipeline_status 和锁
        llm_response_cache=self.llm_response_cache,
    )
    
    # 2. 合并实体和关系（无 pipeline_status）
    await merge_nodes_and_edges(
        chunk_results=chunk_results,
        knowledge_graph_inst=self.chunk_entity_relation_graph,
        entity_vdb=self.entities_vdb,
        relationships_vdb=self.relationships_vdb,
        global_config=asdict(self),
        # 不传递 pipeline_status 和锁
        llm_response_cache=self.llm_response_cache,
    )
    
    # 3. 索引完成回调
    await self._index_done_callback()
    
    # 4. 统计结果
    entities_count = sum(len(nodes) for nodes, _ in chunk_results)
    relations_count = sum(len(edges) for _, edges in chunk_results)
    
    return {
        "status": "success",
        "collection_id": collection_id,
        "chunks_processed": len(chunks),
        "entities_extracted": entities_count,
        "relations_extracted": relations_count,
        "timestamp": datetime.utcnow().isoformat()
    }

async def _index_done_callback(self):
    """索引完成后的回调，确保数据持久化"""
    tasks = [
        storage.index_done_callback()
        for storage in [
            self.entities_vdb,
            self.relationships_vdb,
            self.chunk_entity_relation_graph,
            self.llm_response_cache,
        ]
        if hasattr(storage, 'index_done_callback')
    ]
    await asyncio.gather(*tasks)
```

### 4. 改造后的 ainsert - 保持向后兼容

```python
async def ainsert(
    self,
    input: Union[str, List[str]],
    split_by_character: Optional[str] = None,
    split_by_character_only: bool = False,
    ids: Optional[Union[str, List[str]]] = None,
    file_paths: Optional[Union[str, List[str]]] = None,
) -> None:
    """
    向后兼容的接口，内部调用新的无状态接口
    """
    # 1. 写入文档
    doc_result = await self.ainsert_document(input, ids, file_paths)
    doc_ids = doc_result["doc_ids"]
    
    # 2. 处理每个文档
    all_chunks = []
    
    if isinstance(input, str):
        input = [input]
    if file_paths is None:
        file_paths = ["unknown_source"] * len(input)
    elif isinstance(file_paths, str):
        file_paths = [file_paths]
    
    for doc_id, content, file_path in zip(doc_ids, input, file_paths):
        # 分块
        chunks = await self.aprocess_chunking(
            doc_id, 
            content, 
            file_path,
            split_by_character,
            split_by_character_only
        )
        all_chunks.extend(chunks)
    
    # 3. 构建图索引
    if all_chunks:
        await self.aprocess_graph_indexing(
            all_chunks, 
            self.workspace
        )
```

## 简化的初始化

```python
class LightRAG:
    """无状态化的 LightRAG"""
    
    def __init__(
        self,
        working_dir: str = "./lightrag_cache",
        workspace: str = "default",
        **kwargs
    ):
        self.working_dir = working_dir
        self.workspace = workspace
        
        # 直接初始化配置，不依赖全局状态
        self._init_config(kwargs)
        
        # 同步初始化存储
        self._init_storages_sync()
    
    def _init_config(self, kwargs):
        """初始化配置"""
        # 设置默认值
        self.chunk_token_size = kwargs.get("chunk_token_size", 1200)
        self.chunk_overlap_token_size = kwargs.get("chunk_overlap_token_size", 100)
        self.llm_model_func = kwargs.get("llm_model_func")
        self.embedding_func = kwargs.get("embedding_func")
        # ... 其他配置
    
    def _init_storages_sync(self):
        """同步初始化存储，避免异步初始化的复杂性"""
        # 创建存储实例
        self.full_docs = self._create_kv_storage("full_docs")
        self.text_chunks = self._create_kv_storage("text_chunks")
        self.doc_status = self._create_doc_status_storage()
        
        self.entities_vdb = self._create_vector_storage("entities")
        self.relationships_vdb = self._create_vector_storage("relationships")
        self.chunks_vdb = self._create_vector_storage("chunks")
        
        self.chunk_entity_relation_graph = self._create_graph_storage()
        
        # 不调用 initialize_share_data()
        # 不创建 pipeline_status
        # 不启动后台任务
```

## Celery 任务实现

```python
from celery import Celery
from aperag.graph.lightrag import LightRAG
import asyncio

app = Celery('lightrag_tasks', broker='redis://localhost:6379')

@app.task
def process_document_for_collection(
    document: str,
    doc_id: str,
    collection_id: str,
    file_path: str = "unknown_source"
) -> Dict[str, Any]:
    """处理单个文档的 Celery 任务"""
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 创建无状态 LightRAG 实例
        rag = LightRAG(
            working_dir=f"./lightrag_cache/{collection_id}",
            workspace=collection_id,
            # 传入必要的配置
            llm_model_func=get_llm_func(),
            embedding_func=get_embedding_func(),
        )
        
        # 执行处理流程
        async def process():
            # 1. 写入文档（可选）
            await rag.ainsert_document([document], [doc_id], [file_path])
            
            # 2. 分块
            chunks = await rag.aprocess_chunking(doc_id, document, file_path)
            
            # 3. 构建图索引
            result = await rag.aprocess_graph_indexing(chunks, collection_id)
            
            return result
        
        # 运行异步任务
        result = loop.run_until_complete(process())
        return result
        
    finally:
        loop.close()
        asyncio.set_event_loop(None)

@app.task
def batch_process_collection(
    documents: List[Dict[str, str]],  # [{"content": "", "doc_id": "", "file_path": ""}]
    collection_id: str
) -> List[Dict[str, Any]]:
    """批量处理文档"""
    
    # 为每个文档创建子任务
    tasks = []
    for doc in documents:
        task = process_document_for_collection.delay(
            doc["content"],
            doc["doc_id"],
            collection_id,
            doc.get("file_path", "unknown_source")
        )
        tasks.append(task)
    
    # 收集结果
    results = []
    for task in tasks:
        try:
            result = task.get(timeout=300)  # 5分钟超时
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "error": str(e)
            })
    
    return results
```

## 使用示例

```python
# 1. 直接使用无状态接口
rag = LightRAG(working_dir="./cache", workspace="test_collection")

# 写入文档
doc_result = await rag.ainsert_document(
    ["This is a test document"],
    ["doc1"],
    ["test.txt"]
)

# 分块
chunks = await rag.aprocess_chunking(
    "doc1",
    "This is a test document",
    "test.txt"
)

# 构建图索引
index_result = await rag.aprocess_graph_indexing(chunks, "test_collection")

# 2. 使用 Celery 任务
from aperag.tasks import process_document_for_collection

# 异步处理单个文档
task = process_document_for_collection.delay(
    "This is a test document",
    "doc1",
    "test_collection",
    "test.txt"
)
result = task.get()

# 3. 批量处理
from aperag.tasks import batch_process_collection

documents = [
    {"content": "Doc 1", "doc_id": "doc1", "file_path": "file1.txt"},
    {"content": "Doc 2", "doc_id": "doc2", "file_path": "file2.txt"},
    {"content": "Doc 3", "doc_id": "doc3", "file_path": "file3.txt"},
]

task = batch_process_collection.delay(documents, "test_collection")
results = task.get()
```

## 关键改动总结

1. **接口拆分**：将 `ainsert` 拆分为三个独立接口
2. **移除全局状态**：不使用 `shared_storage.py`
3. **移除文档扫描**：不再有 `apipeline_process_enqueue_documents`
4. **简化初始化**：同步初始化，无后台任务
5. **无状态操作**：每个方法独立运行，不依赖共享状态

这种设计使得 LightRAG 成为真正的无状态服务，可以在分布式环境中自由扩展。 