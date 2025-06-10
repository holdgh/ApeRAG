## 支持用workspace进行数据隔离

### 已完成的改动

1. **基类修改** (aperag/graph/lightrag/base.py)
   - 在 `StorageNameSpace` 基类中添加了 `workspace` 字段
   - 添加了 `storage_type` 属性，用于获取基础的存储类型名称（不含前缀）

2. **namespace.py 简化**
   - 移除了 `make_namespace` 函数，因为不再需要拼接前缀
   - 简化了 `is_namespace` 函数，直接比较namespace而不是检查后缀

3. **LightRAG 主类修改** (lightrag.py)
   - 移除了 `namespace_prefix` 字段
   - 添加了 `workspace` 字段
   - 在创建所有存储实例时传入 `workspace` 参数

4. **PostgreSQL 存储修复** (postgres_impl.py)
   - 修复了SQL模板查找bug，使用 `storage_type` 属性获取正确的SQL模板key
   - PostgreSQL已经支持workspace机制，通过数据库连接的workspace属性实现

5. **文件型存储改造**
   - **JsonKVStorage**: 使用workspace创建目录结构 `{working_dir}/{workspace}/kv_store_{storage_type}.json`
   - **NanoVectorDBStorage**: 使用workspace创建目录结构 `{working_dir}/{workspace}/vdb_{storage_type}.json`
   - **NetworkXStorage**: 使用workspace创建目录结构 `{working_dir}/{workspace}/graph_{storage_type}.graphml`
   - **JsonDocStatusStorage**: 使用workspace创建目录结构 `{working_dir}/{workspace}/kv_store_{storage_type}.json`

6. **lightrag_holder.py 改造**
   - 移除对 `generate_lightrag_namespace_prefix` 的使用
   - 使用 `collection_id` 作为workspace
   - 更新了所有相关的日志信息和缓存key

### 核心改变

- **从namespace_prefix机制改为workspace机制**：不再通过字符串拼接来隔离数据，而是通过workspace字段在存储层实现隔离
- **PostgreSQL bug修复**：解决了SQL模板查找时错误拼接namespace的问题
- **统一的隔离机制**：所有存储类型都使用相同的workspace概念，提高了一致性
- **简化的代码**：移除了复杂的前缀拼接逻辑，代码更加清晰

### 使用方式

现在每个collection都有自己独立的workspace（使用collection.id），所有相关数据都会存储在对应的workspace下：
- 文件型存储：在 `working_dir/{collection_id}/` 目录下
- PostgreSQL：通过workspace字段隔离
- 其他数据库：可以类似PostgreSQL实现workspace字段隔离

---

## 将ainsert拆分为三个独立的无状态接口：

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

---

## Celery任务无状态化改造

### 已完成的改动

1. **新增文件** (aperag/graph/stateless_task_wrapper.py)
   - 创建了 `StatelessLightRAGWrapper` 类，专门用于Celery任务
   - 提供了异步和同步方法：`process_document_async` 和 `process_document_sync`
   - 实现了独立的事件循环管理，避免与Celery冲突
   - 提供了便捷函数：`process_document_for_celery` 和 `delete_document_for_celery`

2. **修改index.py中的Celery任务**
   - **add_lightrag_index_task**：
     - 移除了 `async_to_sync` 和内部异步函数
     - 使用 `process_document_for_celery` 替代原有的 `ainsert` 调用
     - 返回详细的处理结果（chunks数量、实体数量、关系数量）
   - **remove_lightrag_index_task**：
     - 简化实现，移除异步代码
     - 使用 `delete_document_for_celery` 替代 `adelete_by_doc_id`
     - 改进错误处理和日志记录

3. **清理不必要的导入**
   - 从 index.py 中移除了 `async_to_sync` 导入
   - 移除了 `lightrag_holder` 的直接导入

### 核心改变

- **事件循环隔离**：每个Celery任务使用独立的事件循环，完全避免冲突
- **使用无状态接口**：充分利用新的三个无状态接口进行文档处理
- **结构化结果**：返回详细的处理信息，包括chunks、实体、关系的数量
- **更清晰的错误处理**：区分成功、警告和失败状态

### 工作流程

1. **文档处理流程**：
   - 调用 `ainsert_document` 插入文档
   - 调用 `aprocess_chunking` 进行分块
   - 调用 `aprocess_graph_indexing` 构建图索引

2. **事件循环管理**：
   ```python
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   try:
       result = loop.run_until_complete(async_method())
   finally:
       loop.close()
       asyncio.set_event_loop(None)
   ```

### 优势

- **无事件循环冲突**：完全隔离的事件循环管理
- **更好的并发支持**：使用无状态接口，避免全局锁限制
- **详细的处理信息**：返回chunks、实体、关系的具体数量
- **更简洁的代码**：移除了复杂的异步转同步逻辑
- **保持兼容性**：`lightrag_holder.py` 保持不变，确保向后兼容

---

## 删除了本地文件存储

networkx_impl.py
nano_vector_db_impl.py
json_kv_impl.py
json_doc_status_impl.py

---

## 删除pipeline_status全局状态系统

### 已完成的改动

1. **删除全局状态变量** (shared_storage.py)
   - 删除 `pipeline_status` 字典及相关数据结构
   - 删除 `_pipeline_status_lock` 全局锁
   - 删除 `get_pipeline_status_lock()` 函数
   - 删除 `initialize_pipeline_status()` 函数

2. **新增统一日志记录系统** (utils.py)
   - 创建 `LightRAGLogger` 类，提供结构化日志记录
   - 支持自定义前缀和workspace标识
   - 提供专门的进度记录方法：
     - `log_extraction_progress()` - 记录实体关系抽取进度
     - `log_stage_progress()` - 记录文件处理阶段进度
     - `log_entity_merge()` / `log_relation_merge()` - 记录合并操作
   - 添加 `create_lightrag_logger()` 便捷函数

3. **修改核心处理函数** (operate.py)
   - **extract_entities()**：删除pipeline_status参数，使用lightrag_logger记录进度
   - **merge_nodes_and_edges()**：删除pipeline_status参数，使用lightrag_logger记录合并操作
   - **_merge_nodes_then_upsert()** / **_merge_edges_then_upsert()**：删除pipeline_status参数
   - **_handle_entity_relation_summary()**：删除pipeline_status参数

4. **修改主要接口** (lightrag.py)
   - **aprocess_graph_indexing()**：删除pipeline_status使用，创建LightRAGLogger实例
   - **apipeline_process_enqueue_documents()**：重构为使用LightRAGLogger的清晰日志记录
   - 删除所有pipeline_status相关的导入和引用

5. **清理相关函数** (shared_storage.py)
   - 删除 `clean_up_pipeline_status()`
   - 删除 `finalize_storage_data()` 中的pipeline_status处理
   - 删除 `cleanup_namespace_data()` 中的pipeline_status清理

### 核心改变

- **从全局状态改为无状态日志**：不再依赖共享的pipeline_status字典，使用独立的日志记录器
- **消除并发瓶颈**：删除_pipeline_status_lock全局锁，允许真正的并发处理
- **统一日志格式**：所有进度信息使用一致的格式和前缀，便于监控和调试
- **可配置的日志前缀**：支持自定义日志前缀，适应不同的使用场景

### 日志示例

```python
# 创建日志记录器
lightrag_logger = create_lightrag_logger(prefix="LightRAG-GraphIndex", workspace="collection_123")

# 记录不同类型的进度
lightrag_logger.log_extraction_progress(1, 10, 5, 3)  # 块进度
lightrag_logger.log_entity_merge("Person", 3, 1, True)  # 实体合并
lightrag_logger.error("Processing failed", exc_info=True)  # 错误信息
```

### 优势

- **真正的并发支持**：删除全局锁后，多个collection可以并发处理
- **更好的监控能力**：结构化日志便于集成监控系统
- **简化的代码**：移除复杂的全局状态管理逻辑
- **更好的调试体验**：清晰的日志格式和workspace隔离

---

## 清理shared_storage.py全局状态管理

### 已完成的改动

1. **删除废弃的全局变量**
   - `_shared_dicts` - 命名空间共享字典管理
   - `_init_flags` / `_update_flags` - 初始化和更新标志
   - `_internal_lock` / `_data_init_lock` - 已不再使用的锁
   - `_workers` / `_manager` - 多进程管理相关变量

2. **删除废弃的函数**
   - `get_internal_lock()` / `get_data_init_lock()` - 锁获取函数
   - `get_namespace_data()` / `reset_namespace_data()` - 命名空间数据管理
   - `cleanup_namespace_data()` / `finalize_storage_data()` - 清理函数
   - 所有pipeline_status相关的管理函数

3. **简化UnifiedLock类**
   - 移除复杂的多层锁机制（async_lock辅助锁）
   - 简化为单一锁的统一接口
   - 保留向后兼容的同步上下文管理器支持

4. **精简initialize_share_data()函数**
   - 只初始化必要的存储锁和图数据库锁
   - 移除复杂的共享数据管理逻辑
   - 保持单进程/多进程模式的兼容性

### 保留的核心功能

- **_storage_lock** - 文件存储操作保护（JsonKVStorage等）
- **_graph_db_lock** - 图数据库原子操作保护
- **get_storage_lock()** / **get_graph_db_lock()** - 锁获取接口
- **UnifiedLock类** - 统一的异步/同步锁接口
- **initialize_share_data()** - 基础锁初始化

### 核心改变

- **最小化全局状态**：只保留必要的数据保护锁，删除所有管道状态管理
- **简化锁机制**：从复杂的多层锁简化为直接的单一锁机制
- **移除命名空间管理**：所有相关的全局共享数据管理都已移除
- **代码大幅精简**：从310行减少到约150行，移除了近50%的代码

### 清理效果

- **文件大小减少**：shared_storage.py从310行减少到约150行
- **更清晰的职责**：文件现在只负责基础的锁管理，职责单一
- **更好的维护性**：删除了复杂的全局状态管理，降低了维护成本
- **保持兼容性**：核心的锁接口保持不变，不影响现有功能

### 当前架构

```python
# 现在的shared_storage.py只包含：
- 基础锁类型定义
- UnifiedLock统一锁接口
- 两个数据保护锁：storage_lock, graph_db_lock  
- 基础的锁初始化函数
- 直接的日志记录工具
```

这次清理彻底移除了LightRAG中的复杂全局状态管理，实现了真正的无状态架构。

## 进一步简化shared_storage.py架构

### 已完成的改动

1. **完全删除UnifiedLock抽象类**
   - 移除了复杂的统一锁接口
   - 删除了对多进程锁和异步锁的抽象封装
   - 简化为直接使用`asyncio.Lock`

2. **移除多进程支持**
   - 删除所有`multiprocessing.Manager`相关代码
   - 移除`workers`参数和多进程判断逻辑
   - 删除`ProcessLock`和相关类型定义
   - 统一使用`asyncio.Lock`进行并发控制

3. **精简函数接口**
   - `get_graph_db_lock()` 直接返回`asyncio.Lock`对象
   - 删除`enable_logging`参数，简化函数签名
   - `initialize_share_data()` 不再需要`workers`参数

4. **代码大幅简化**
   - 文件从183行减少到约50行，减少了70%以上的代码
   - 移除了100+行的UnifiedLock类定义
   - 删除了复杂的多进程初始化逻辑

5. **更新所有调用点**
   - 修改`utils_graph.py`中7个函数的锁获取调用
   - 修改`operate.py`中的锁获取调用
   - 删除所有`enable_logging=False`参数传递

### 简化后的架构

```python
# 现在的shared_storage.py只包含：
- 一个全局asyncio.Lock: _graph_db_lock
- 一个简单的获取函数: get_graph_db_lock()
- 一个基础初始化函数: initialize_share_data()
- 直接的日志记录工具: direct_log()
```

### 使用方式对比

**之前（复杂）：**
```python
graph_db_lock = get_graph_db_lock(enable_logging=False)
async with graph_db_lock:  # UnifiedLock.__aenter__()
    # 数据库操作
```

**现在（简洁）：**
```python
graph_db_lock = get_graph_db_lock()  
async with graph_db_lock:  # 直接使用asyncio.Lock
    # 数据库操作
```

### 核心优势

- **极简架构**：移除所有不必要的抽象层，直接使用标准库
- **单一职责**：文件现在只负责基础的图数据库锁管理
- **更好的性能**：去除抽象层开销，直接使用asyncio.Lock
- **易于维护**：代码减少70%，逻辑清晰简单
- **完全异步**：统一使用async/await模式，无同步兼容包袱

### 删除的复杂特性

- ❌ 多进程支持（Manager, ProcessLock）
- ❌ 统一锁接口（UnifiedLock类）
- ❌ 同步锁兼容（__enter__/__exit__）
- ❌ 调试日志选项（enable_logging参数）
- ❌ 复杂的锁层级（辅助锁、内部锁等）

现在LightRAG的锁管理变得极其简洁，只保留了必要的图数据库操作保护，完全符合单进程异步架构的需求。

## 最终简化shared_storage.py

### 已完成的改动

1. **删除不必要的保护机制**
   - 删除 `_initialized` 全局变量及其检查逻辑
   - 删除 `direct_log` 函数，使用标准 logger.debug() 替代
   - 移除 `sys` 模块导入

2. **精简初始化逻辑**
   - `initialize_share_data()` 函数不再检查重复初始化
   - 每次调用都直接创建新的 `asyncio.Lock()`
   - 简化为最小化的锁管理

### 简化理由

- **过度保护**：`_initialized` 只保护一个轻量级 `asyncio.Lock()` 的创建，成本极低
- **功能重复**：`direct_log` 与标准 logger 功能重复，增加不必要的复杂性
- **更清晰的代码**：删除后代码从51行减少到约20行，职责更加单一

### 最终架构

```python
# 现在的shared_storage.py只包含：
- 一个全局锁变量：_graph_db_lock
- 一个获取函数：get_graph_db_lock()
- 一个初始化函数：initialize_share_data()
- 标准日志记录：logger.debug()
```

**最终成果**：完全删除了 shared_storage.py 文件，将锁管理转移到 LightRAG 实例级别，彻底实现了无状态化目标。

## 彻底删除shared_storage.py

### 最终实现的完整改造

1. **全局锁 → 实例级锁**
   - 在 `LightRAG.__post_init__()` 中创建 `self._graph_db_lock = asyncio.Lock()`
   - 移除对 `initialize_share_data()` 的调用
   - 删除 `from aperag.graph.lightrag.kg.shared_storage import` 导入

2. **utils_graph.py 函数签名改造**
   - 所有函数添加 `graph_db_lock: asyncio.Lock | None = None` 参数
   - 使用 `_get_lock_or_create()` 辅助函数处理锁获取
   - 保持向后兼容性，可以创建本地锁

3. **operate.py 中的调用更新**
   - `merge_nodes_and_edges()` 函数接受可选的 `graph_db_lock` 参数
   - 在 LightRAG 中调用时传入 `self._graph_db_lock`

4. **彻底删除shared_storage.py**
   - 删除整个文件，包含28行代码
   - 移除全局状态管理
   - 消除进程间锁冲突的可能性

### 技术优势

**存储系统原生支持**：你使用的存储架构本身就有完善的并发控制
- **Neo4j**：ACID事务，内置并发控制
- **PostgreSQL**：成熟的MVCC机制
- **Qdrant**：现代向量数据库，支持并发操作

**实例级锁的好处**：
- 🚀 **性能提升**：避免全局锁竞争，不同LightRAG实例之间完全独立
- 🔧 **更好的架构**：每个实例管理自己的锁，符合面向对象设计
- 🛡️ **进程安全**：消除了Celery多进程环境中的锁冲突
- ⚡ **无状态化**：实例创建即可用，无需全局初始化

### 架构演进总结

```
原架构: 全局锁 + shared_storage.py (51行)
  ↓ 简化阶段1: 删除过度保护 (28行)
  ↓ 简化阶段2: 实例级锁管理
  ↓ 最终阶段: 完全删除 (0行)

现架构: LightRAG实例锁 + 可选参数传递
```

**最终状态**：LightRAG现在完全无状态，每个实例独立管理锁资源，没有任何全局共享状态，完美契合现代多进程、多实例的部署环境！

## 修复锁一致性问题

### 问题发现
在删除 shared_storage.py 后，发现了锁一致性问题：
- `merge_nodes_and_edges()` 使用实例级锁 `self._graph_db_lock`
- `utils_graph.py` 函数使用 `_get_lock_or_create(None)` 创建新的本地锁
- **结果**：两个地方使用了不同的锁，破坏了同步机制

### 修复方案
**问题根因**：在 LightRAG 类中调用 `utils_graph.py` 函数时，没有传入实例级锁。

**解决方法**：在所有调用 `utils_graph.py` 函数的地方传入 `graph_db_lock=self._graph_db_lock`：

```python
# 修复前
await adelete_by_entity(
    self.chunk_entity_relation_graph,
    self.entities_vdb,
    self.relationships_vdb,
    entity_name,
)

# 修复后
await adelete_by_entity(
    self.chunk_entity_relation_graph,
    self.entities_vdb,
    self.relationships_vdb,
    entity_name,
    graph_db_lock=self._graph_db_lock,  # ✅ 传入实例级锁
)
```

### 修复的函数
所有 LightRAG 类中对 `utils_graph.py` 函数的调用都已修复：
- `adelete_by_entity()`
- `adelete_by_relation()`
- `aedit_entity()`
- `aedit_relation()`
- `acreate_entity()`
- `acreate_relation()`
- `amerge_entities()`

### 最终一致性
现在所有图操作使用统一的实例级锁：
- `merge_nodes_and_edges()` ← `self._graph_db_lock`
- `utils_graph.py` 函数 ← `self._graph_db_lock`
- 保证了数据一致性和操作原子性

--- 

