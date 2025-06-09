# LightRAG 代码改造计划

## 1. 核心问题定位

### 1.1 全局状态管理问题

**问题模块**: `aperag/graph/lightrag/kg/shared_storage.py`

**具体问题**:
```python
# 模块级全局变量导致无法多实例运行
_is_multiprocess = None
_manager = None
_shared_dicts: Optional[Dict[str, Any]] = None
_pipeline_status_lock: Optional[LockType] = None
_storage_lock: Optional[LockType] = None
_graph_db_lock: Optional[LockType] = None
_initialized = None
```

**影响**:
- 同一进程内所有 LightRAG 实例共享这些全局变量
- 创建第二个实例时，`initialize_share_data()` 会直接返回，使用第一个实例的配置
- 多个 collection 会互相干扰，共享管道状态

### 1.2 管道状态串行化问题

**问题模块**: `aperag/graph/lightrag/lightrag.py` 的 `apipeline_process_enqueue_documents` 方法

**具体问题**:
```python
# Line 855-890
pipeline_status = await get_namespace_data("pipeline_status")  # 全局共享
pipeline_status_lock = get_pipeline_status_lock()              # 全局锁

async with pipeline_status_lock:
    if not pipeline_status.get("busy", False):
        pipeline_status["busy"] = True  # 阻止所有其他实例
        # 处理文档...
    else:
        pipeline_status["request_pending"] = True
        return  # 其他实例直接返回
```

**影响**:
- 即使创建多个 LightRAG 实例，同一时刻只有一个能执行 `ainsert`
- `max_parallel_insert` 只控制单个批次内的并发，不能实现真正的多实例并发

### 1.3 异步初始化缺陷

**问题模块**: `aperag/graph/lightrag/lightrag.py` 的 `__post_init__` 和 `_run_async_safely` 方法

**具体问题**:
```python
# Line 450-474
def __post_init__(self):
    # ...
    if self.auto_manage_storages_states:
        self._run_async_safely(self.initialize_storages, "Storage Initialization")

def _run_async_safely(self, async_func, action_name=""):
    loop = always_get_an_event_loop()
    if loop.is_running():
        # 创建后台任务但不等待！
        task = loop.create_task(async_func())
        task.add_done_callback(lambda t: logger.info(f"{action_name} completed!"))
        # 对象立即返回，可能未初始化完成
    else:
        loop.run_until_complete(async_func())
```

**影响**:
- 在异步环境中创建 LightRAG 时返回未完全初始化的对象
- 立即使用会导致 `AttributeError` 或其他不可预测的错误

### 1.4 存储实例耦合问题

**问题模块**: 各种存储实现（`json_kv_impl.py`, `networkx_impl.py` 等）

**具体问题**:
- 存储实例绑定了 `namespace_prefix`，无法动态切换
- 缺少存储池化机制，每个实例都创建新的存储连接
- 文件存储路径硬编码，难以适配多租户场景

## 2. 改造方案

### 2.1 移除全局状态管理

**目标**: 将所有全局状态改为实例级别

**改造模块**: 
- 删除 `shared_storage.py` 中的全局变量
- 改造为实例级的状态管理器

**新设计**:
```python
# aperag/graph/lightrag/instance_state.py
class InstanceStateManager:
    """实例级状态管理器，替代全局状态"""
    
    def __init__(self, namespace: str, workers: int = 1):
        self.namespace = namespace
        self.workers = workers
        self._is_multiprocess = workers > 1
        
        # 实例级锁
        if self._is_multiprocess:
            self._manager = Manager()
            self._storage_lock = self._manager.Lock()
            self._pipeline_lock = self._manager.Lock()
            self._graph_lock = self._manager.Lock()
        else:
            self._storage_lock = asyncio.Lock()
            self._pipeline_lock = asyncio.Lock()
            self._graph_lock = asyncio.Lock()
        
        # 实例级状态
        self._pipeline_status = {
            "busy": False,
            "job_name": "",
            "docs": 0,
            "cur_batch": 0,
        }
        
        # 实例级存储状态
        self._storage_initialized = {}
```

**修改 LightRAG 类**:
```python
@dataclass
class LightRAG:
    # ... 原有字段 ...
    
    # 添加实例级状态管理
    _state_manager: InstanceStateManager = field(init=False)
    
    def __post_init__(self):
        # 创建实例级状态管理器
        self._state_manager = InstanceStateManager(
            namespace=self.namespace_prefix,
            workers=1  # 始终使用单进程模式
        )
        
        # 使用实例级状态初始化存储
        self._initialize_storages_sync()
```

### 2.2 重构管道处理逻辑

**目标**: 移除全局 pipeline_status，实现真正的并发处理

**改造模块**: `lightrag.py` 的 `apipeline_process_enqueue_documents` 方法

**新设计**:
```python
async def apipeline_process_enqueue_documents(
    self,
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
) -> None:
    """重构后的文档处理管道，支持并发"""
    
    # 使用实例级管道状态
    pipeline_status = self._state_manager.get_pipeline_status()
    
    # 获取待处理文档（不使用全局锁）
    to_process_docs = await self._get_pending_documents()
    
    if not to_process_docs:
        logger.info(f"[{self.namespace_prefix}] No documents to process")
        return
    
    # 使用信号量控制并发，而非全局锁
    semaphore = asyncio.Semaphore(self.max_parallel_insert)
    
    async def process_document_concurrent(doc_id: str, status_doc: DocProcessingStatus):
        async with semaphore:
            try:
                # 处理单个文档
                await self._process_single_document(
                    doc_id, status_doc, 
                    split_by_character, split_by_character_only
                )
            except Exception as e:
                logger.error(f"[{self.namespace_prefix}] Failed to process {doc_id}: {e}")
                await self._mark_document_failed(doc_id, str(e))
    
    # 真正的并发处理
    tasks = [
        process_document_concurrent(doc_id, doc) 
        for doc_id, doc in to_process_docs.items()
    ]
    
    await asyncio.gather(*tasks, return_exceptions=True)
```

### 2.3 修复异步初始化问题

**目标**: 确保 LightRAG 实例创建时同步完成初始化

**改造模块**: `__post_init__` 方法

**新设计**:
```python
def __post_init__(self):
    """同步初始化，确保对象完全可用"""
    # 1. 初始化状态管理器
    self._state_manager = InstanceStateManager(self.namespace_prefix)
    
    # 2. 同步初始化存储
    self._initialize_storages_sync()
    
    # 3. 标记初始化完成
    self._initialized = True

def _initialize_storages_sync(self):
    """同步初始化所有存储"""
    # 创建存储实例
    self.llm_response_cache = self._create_kv_storage("llm_cache")
    self.full_docs = self._create_kv_storage("full_docs")
    self.text_chunks = self._create_kv_storage("text_chunks")
    self.entities_vdb = self._create_vector_storage("entities")
    self.relationships_vdb = self._create_vector_storage("relationships")
    self.chunks_vdb = self._create_vector_storage("chunks")
    self.chunk_entity_relation_graph = self._create_graph_storage("entity_relation")
    self.doc_status = self._create_doc_status_storage("doc_status")
    
    # 同步初始化存储（不使用异步）
    for storage in self._get_all_storages():
        storage.initialize_sync()  # 新增同步初始化方法

async def initialize_storages_async(self):
    """提供异步初始化选项，但不在构造函数中调用"""
    if not self._initialized:
        raise RuntimeError("Must call __post_init__ first")
    
    # 异步初始化逻辑...
```

### 2.4 实现存储池化机制

**目标**: 避免重复创建存储连接，支持存储实例复用

**新增模块**: `storage_pool.py`

```python
# aperag/graph/lightrag/storage_pool.py
from typing import Dict, Any, Optional
import asyncio
from weakref import WeakValueDictionary

class StoragePool:
    """存储实例池，支持复用和生命周期管理"""
    
    def __init__(self):
        # 使用弱引用避免内存泄漏
        self._kv_storages: WeakValueDictionary = WeakValueDictionary()
        self._vector_storages: WeakValueDictionary = WeakValueDictionary()
        self._graph_storages: WeakValueDictionary = WeakValueDictionary()
        self._lock = asyncio.Lock()
    
    async def get_kv_storage(
        self, 
        storage_type: str, 
        namespace: str,
        config: Dict[str, Any]
    ) -> BaseKVStorage:
        """获取或创建 KV 存储实例"""
        key = f"{storage_type}:{namespace}"
        
        async with self._lock:
            storage = self._kv_storages.get(key)
            if storage is None:
                storage = self._create_kv_storage(storage_type, namespace, config)
                self._kv_storages[key] = storage
            
            return storage
    
    def _create_kv_storage(
        self,
        storage_type: str,
        namespace: str, 
        config: Dict[str, Any]
    ) -> BaseKVStorage:
        """创建新的 KV 存储实例"""
        if storage_type == "JsonKVStorage":
            from .kg.json_kv_impl import JsonKVStorage
            return JsonKVStorage(namespace=namespace, global_config=config)
        elif storage_type == "PGKVStorage":
            from .kg.postgres_impl import PGKVStorage
            return PGKVStorage(namespace=namespace, global_config=config)
        # ... 其他存储类型

# 全局存储池（这是唯一允许的全局对象）
_storage_pool = StoragePool()

def get_storage_pool() -> StoragePool:
    return _storage_pool
```

### 2.5 重构存储实现

**目标**: 使存储实现支持命名空间切换和连接复用

**改造示例**: `json_kv_impl.py`

```python
class JsonKVStorage(BaseKVStorage):
    def __init__(self, namespace: str, global_config: dict[str, Any]):
        super().__init__(namespace, global_config)
        self._cache = {}  # 内存缓存
        self._file_lock = asyncio.Lock()
        self._initialized = False
    
    def initialize_sync(self):
        """同步初始化"""
        if self._initialized:
            return
        
        # 创建存储目录
        os.makedirs(self._get_storage_path(), exist_ok=True)
        
        # 加载已有数据
        self._load_from_disk()
        
        self._initialized = True
    
    async def initialize(self):
        """异步初始化（兼容旧接口）"""
        self.initialize_sync()
    
    def _get_storage_path(self) -> str:
        """动态计算存储路径"""
        base_dir = self.global_config.get("working_dir", "./lightrag_cache")
        return os.path.join(base_dir, "kv_store", self.namespace)
    
    async def switch_namespace(self, new_namespace: str):
        """切换命名空间"""
        async with self._file_lock:
            # 保存当前数据
            await self._save_to_disk()
            
            # 切换命名空间
            self.namespace = new_namespace
            
            # 重新加载数据
            self._load_from_disk()
```

## 3. 实施步骤

### 第一阶段：解耦全局状态（优先级：高）

1. **创建 `instance_state.py`**
   - 实现 `InstanceStateManager` 类
   - 提供实例级的锁和状态管理

2. **修改 `lightrag.py`**
   - 在 `__post_init__` 中创建实例级状态管理器
   - 替换所有对 `shared_storage` 的引用

3. **删除或重构 `shared_storage.py`**
   - 保留必要的工具函数
   - 移除所有全局变量

### 第二阶段：修复并发问题（优先级：高）

1. **重构 `apipeline_process_enqueue_documents`**
   - 移除全局 pipeline_status 检查
   - 实现基于信号量的并发控制

2. **修改文档状态管理**
   - 使用数据库级别的原子操作
   - 避免内存状态共享

### 第三阶段：优化存储层（优先级：中）

1. **实现存储池**
   - 创建 `storage_pool.py`
   - 支持存储实例复用

2. **改造存储实现**
   - 添加 `initialize_sync` 方法
   - 支持命名空间动态切换

### 第四阶段：完善错误处理（优先级：低）

1. **添加初始化状态检查**
   - 在所有公开方法中检查初始化状态
   - 提供清晰的错误信息

2. **实现优雅降级**
   - 部分存储失败时继续运行
   - 提供降级模式配置

## 4. 兼容性考虑

### 保持 API 兼容

```python
# 提供兼容层
class LightRAG:
    @classmethod
    def create_async(cls, **kwargs) -> Awaitable['LightRAG']:
        """异步创建方法，完全初始化后返回"""
        instance = cls(**kwargs)
        await instance.initialize_storages_async()
        return instance
    
    def insert(self, *args, **kwargs):
        """同步接口保持不变"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.ainsert(*args, **kwargs))
        finally:
            loop.close()
```

### 配置迁移

```python
# 支持旧配置格式
if "namespace_prefix" in kwargs and "namespace" not in kwargs:
    kwargs["namespace"] = kwargs.pop("namespace_prefix")
```

## 5. 测试策略

### 单元测试

```python
# tests/test_concurrent_instances.py
async def test_multiple_instances_concurrent():
    """测试多实例并发处理"""
    instances = [
        LightRAG(namespace_prefix=f"test_{i}")
        for i in range(5)
    ]
    
    # 并发插入文档
    tasks = [
        instance.ainsert([f"Document for instance {i}"])
        for i, instance in enumerate(instances)
    ]
    
    results = await asyncio.gather(*tasks)
    assert all(results)  # 所有实例都应成功
```

### 性能测试

```python
# tests/test_performance.py
async def test_throughput_improvement():
    """测试改造后的吞吐量提升"""
    # 测试单实例串行处理
    single_instance_time = await measure_single_instance_time()
    
    # 测试多实例并发处理
    multi_instance_time = await measure_multi_instance_time()
    
    # 期望至少3倍性能提升
    assert multi_instance_time < single_instance_time / 3
```

## 6. 风险与缓解

### 风险1：破坏现有功能
- **缓解**: 保持原有 API，提供兼容层
- **测试**: 完整的回归测试套件

### 风险2：性能下降
- **缓解**: 实现存储池化，减少重复初始化
- **监控**: 添加性能指标采集

### 风险3：数据一致性
- **缓解**: 使用数据库事务，避免内存状态
- **验证**: 并发场景下的数据一致性测试