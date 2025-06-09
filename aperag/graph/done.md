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

