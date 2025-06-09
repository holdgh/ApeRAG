# LightRAG 渐进式改造详细计划

## 改造原则
1. **保持核心逻辑不变**：不修改 operate.py 中的算法逻辑
2. **渐进式改造**：每个步骤可独立实现和测试
3. **向后兼容**：每个阶段都保持 API 兼容性
4. **最小化破坏**：优先使用包装器和适配器模式

## 改造路线图

### 第一阶段：基础设施准备（不破坏任何现有功能）

#### 1.1 创建存储抽象层
**目标**：在不修改现有存储实现的情况下，创建统一的存储接口

##### 1.1.1 创建存储协议定义
```python
# aperag/graph/storage_protocol.py
```
- [ ] 定义 `StorageProtocol` 基类
- [ ] 定义 `CollectionAwareStorage` 接口
- [ ] 定义 `StorageFactory` 工厂类

##### 1.1.2 创建存储适配器
```python
# aperag/graph/storage_adapter.py
```
- [ ] 创建 `LightRAGStorageAdapter` 类，包装现有存储
- [ ] 实现 collection_id 到 namespace_prefix 的映射
- [ ] 添加存储实例缓存机制

##### 1.1.3 测试存储适配器
- [ ] 编写单元测试验证适配器功能
- [ ] 确保不影响现有 LightRAG 功能

#### 1.2 创建函数式接口包装器
**目标**：提供简单的函数调用接口，内部仍使用 LightRAG

##### 1.2.1 创建知识提取接口
```python
# aperag/graph/knowledge_extraction.py
```
- [ ] 实现 `extract_knowledge_and_store` 函数
- [ ] 内部调用 LightRAG 的功能
- [ ] 支持函数注入（llm_func, embedding_func）

##### 1.2.2 创建查询接口
```python
# aperag/graph/knowledge_query.py
```
- [ ] 实现 `query_knowledge` 函数
- [ ] 包装 LightRAG 的查询功能
- [ ] 支持多种查询模式

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

#### 3.1 设计 Collection 管理器
**目标**：实现真正的 collection 级别隔离

##### 3.1.1 创建 Collection 管理器
```python
# aperag/graph/collection_manager.py
```
- [ ] 实现 `CollectionManager` 类
- [ ] 管理 collection 到存储的映射
- [ ] 实现 collection 级别的配置

##### 3.1.2 改造存储命名空间
- [ ] 修改 `make_namespace` 函数支持 collection_id
- [ ] 创建 collection_id 到 namespace 的转换规则
- [ ] 保持向后兼容性

##### 3.1.3 实现 Collection 上下文
```python
# aperag/graph/collection_context.py
```
- [ ] 创建 `CollectionContext` 上下文管理器
- [ ] 自动处理存储切换
- [ ] 支持批量操作

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