# LightRAG 渐进式改造详细计划

## 改造原则
1. **保持核心逻辑不变**：不修改 operate.py 中的算法逻辑
2. **渐进式改造**：每个步骤可独立实现和测试
3. **向后兼容**：每个阶段都保持 API 兼容性
4. **最小化破坏**：优先使用包装器和适配器模式

## 改造路线图


### 第二阶段：状态管理改造（逐步移除全局状态）

#### 2.1 创建实例级状态管理器
**目标**：替代 shared_storage.py 的全局变量，但保持接口兼容

##### 2.1.1 实现状态管理器
```python
# aperag/graph/lightrag/instance_state.py
```
- [ ] 创建 `InstanceStateManager` 类
- [ ] 实现锁管理（单进程/多进程）
- [ ] 实现状态存储（pipeline_status 等）

##### 2.1.2 创建兼容层
```python
# aperag/graph/lightrag/kg/shared_storage_compat.py
```
- [ ] 保留原有的函数接口
- [ ] 内部重定向到实例级状态管理器
- [ ] 添加废弃警告

##### 2.1.3 修改 LightRAG 初始化
**文件**：`aperag/graph/lightrag/lightrag.py`
- [ ] 在 `__post_init__` 中创建 `InstanceStateManager`
- [ ] 修改存储初始化逻辑，使用实例状态
- [ ] 保持原有 API 不变

#### 2.2 重构全局锁机制
**目标**：将全局锁改为实例级锁

##### 2.2.1 识别所有使用全局锁的地方
- [ ] 搜索 `get_pipeline_status_lock()`
- [ ] 搜索 `get_storage_lock()`
- [ ] 搜索 `get_graph_db_lock()`

##### 2.2.2 创建锁代理
```python
# aperag/graph/lightrag/lock_proxy.py
```
- [ ] 实现 `LockProxy` 类
- [ ] 支持从全局锁迁移到实例锁
- [ ] 添加锁使用统计

##### 2.2.3 逐步替换锁调用
- [ ] 先在新代码中使用实例锁
- [ ] 添加配置开关控制锁类型
- [ ] 逐步迁移旧代码

### 第三阶段：Collection 隔离机制实现

#### 3.1 collection 级别隔离
**目标**：实现真正的 collection 级别隔离

我想要删掉目前的namespace_prefix机制。
目前JsonKVStorage,NanoVectorDBStorage,NetworkXStorage,JsonDocStatusStorage可以按照namespace prefix隔离，neo4j之类的应该也是可以的。
但是pg结合namespace prefix有严重bug, "sql = SQL_TEMPLATES["get_by_id_" + self.namespace]"会把namespace prefix也拼接进去，导致无法获得要执行的SQL。
我希望你能够帮我用workspace机制替代namespace prefix机制（目前pg已经有了，但是我希望能够推广到所有的db），workspace可以理解为collection的概念。

#### 3.2 改造文档处理流程
**目标**：支持按 collection 并发处理

##### 3.2.1 重构管道处理
**文件**：`aperag/graph/lightrag/lightrag.py`
- [ ] 修改 `apipeline_process_enqueue_documents`
- [ ] 移除全局 pipeline_status 检查
- [ ] 使用 collection 级别的队列

##### 3.2.2 实现并发控制
- [ ] 使用 asyncio.Semaphore 替代全局锁
- [ ] 支持 collection 级别的并发限制
- [ ] 添加并发监控

### 第四阶段：存储层解耦

#### 4.1 创建存储接口层
**目标**：定义统一的存储接口，隐藏实现细节

##### 4.1.1 定义存储接口
```python
# aperag/storage/interfaces.py
```
- [ ] 定义 `IKVStorage` 接口
- [ ] 定义 `IVectorStorage` 接口
- [ ] 定义 `IGraphStorage` 接口

##### 4.1.2 实现存储工厂
```python
# aperag/storage/factory.py
```
- [ ] 创建存储工厂类
- [ ] 支持注册自定义存储实现
- [ ] 提供默认实现（使用 LightRAG 存储）

#### 4.2 实现外部存储适配器
**目标**：支持使用外部数据库

##### 4.2.1 PostgreSQL 适配器
```python
# aperag/storage/postgres_adapter.py
```
- [ ] 实现 KV 存储接口
- [ ] 实现向量存储接口（使用 pgvector）
- [ ] 支持事务

##### 4.2.2 Neo4j 适配器
```python
# aperag/storage/neo4j_adapter.py
```
- [ ] 实现图存储接口
- [ ] 支持批量操作
- [ ] 优化查询性能

### 第五阶段：核心算法提取

#### 5.1 提取文档处理算法
**目标**：将算法与存储分离

##### 5.1.1 创建算法模块
```python
# aperag/graph/algorithms/chunking.py
```
- [ ] 提取 `chunking_by_token_size` 逻辑
- [ ] 创建无状态的分块器类
- [ ] 添加更多分块策略

##### 5.1.2 提取实体抽取算法
```python
# aperag/graph/algorithms/extraction.py
```
- [ ] 提取实体抽取逻辑
- [ ] 创建可配置的抽取器
- [ ] 支持自定义 prompt

#### 5.2 创建轻量级包装器
**目标**：只保留必要的 LightRAG 功能

##### 5.2.1 创建核心包装器
```python
# aperag/graph/lightrag_core.py
```
- [ ] 只包含核心算法调用
- [ ] 移除所有存储依赖
- [ ] 提供简单的 API

### 第六阶段：最终整合与优化

#### 6.1 创建新的统一接口
**目标**：提供简洁、易用的 API

##### 6.1.1 实现主接口
```python
# aperag/graph/api.py
```
- [ ] 整合所有功能
- [ ] 提供流式接口
- [ ] 支持批处理

##### 6.1.2 迁移工具
```python
# aperag/graph/migration.py
```
- [ ] 提供从旧 API 到新 API 的迁移工具
- [ ] 自动转换配置
- [ ] 数据迁移支持

#### 6.2 性能优化
- [ ] 实现连接池
- [ ] 添加缓存层
- [ ] 优化并发性能

## 实施时间表

### 第1-2周：基础设施准备
- 完成存储抽象层
- 实现函数式接口
- 不影响现有功能

### 第3-4周：状态管理改造
- 实现实例级状态管理
- 创建兼容层
- 开始移除全局状态

### 第5-6周：Collection 隔离
- 实现 Collection 管理器
- 改造处理流程
- 支持并发处理

### 第7-8周：存储层解耦
- 定义存储接口
- 实现外部存储适配器
- 测试存储切换

### 第9-10周：核心算法提取
- 提取算法模块
- 创建轻量级包装器
- 优化性能

### 第11-12周：整合与发布
- 创建统一 API
- 完善文档
- 性能测试

## 测试策略

### 单元测试
每个模块都需要独立的单元测试：
- [ ] 存储适配器测试
- [ ] 状态管理器测试
- [ ] Collection 管理器测试
- [ ] 算法模块测试

### 集成测试
- [ ] 端到端处理流程测试
- [ ] 并发处理测试
- [ ] 存储切换测试
- [ ] 性能基准测试

### 兼容性测试
- [ ] 确保旧 API 继续工作
- [ ] 测试迁移工具
- [ ] 验证数据兼容性

## 风险管理

### 技术风险
1. **全局状态耦合**
   - 缓解：逐步替换，保留兼容层
   - 监控：添加状态使用追踪

2. **性能下降**
   - 缓解：实现缓存和连接池
   - 监控：建立性能基准

3. **数据一致性**
   - 缓解：使用事务和锁
   - 监控：添加一致性检查

### 项目风险
1. **时间估算不准**
   - 缓解：每阶段设置缓冲时间
   - 监控：每周进度评审

2. **需求变更**
   - 缓解：保持灵活的架构
   - 监控：定期与用户沟通

## 成功标准

1. **功能完整性**
   - 所有现有功能继续工作
   - 新 API 覆盖所有用例

2. **性能指标**
   - 并发处理能力提升 3x
   - 内存使用降低 50%

3. **可维护性**
   - 代码覆盖率 > 80%
   - 文档完整性 100%

4. **用户体验**
   - API 调用简化 70%
   - 错误信息清晰度提升

## 改造完成总结

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