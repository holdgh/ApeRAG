# LightRAG 渐进式改造详细计划

## 改造原则
1. **保持核心逻辑不变**：不修改 operate.py 中的算法逻辑
2. **渐进式改造**：每个步骤可独立实现和测试
3. **向后兼容**：每个阶段都保持 API 兼容性
4. **最小化破坏**：优先使用包装器和适配器模式

## 🚨 第一阶段：解决并发问题和Celery集成（紧急）

### 1.1 问题诊断
基于代码分析，发现三个核心问题：

#### 问题1：全局状态冲突
- `shared_storage.py` 使用模块级全局变量（`_shared_dicts`, `_pipeline_status_lock`等）
- 所有LightRAG实例共享这些全局状态，导致无法并发

#### 问题2：管道互斥锁
```python
# lightrag.py - apipeline_process_enqueue_documents
async with pipeline_status_lock:
    if not pipeline_status.get("busy", False):
        pipeline_status["busy"] = True  # 全局互斥！
    else:
        return  # 其他实例直接返回
```

#### 问题3：事件循环管理冲突
- `always_get_an_event_loop()` 在Celery环境中会创建新的事件循环
- `_run_async_safely` 创建后台任务但不等待，导致初始化不完整

### 1.2 具体解决方案

#### 步骤1：创建实例级状态管理器（Week 1）

**创建新文件** `aperag/graph/lightrag/instance_state.py`:
```python
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class InstanceStateManager:
    """实例级状态管理器，替代全局状态"""
    workspace: str
    
    # 实例级锁
    _pipeline_status_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _storage_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _graph_db_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    # 实例级状态
    _pipeline_status: Dict[str, Any] = field(default_factory=lambda: {
        "busy": False,
        "job_name": "-",
        "job_start": None,
        "docs": 0,
        "batchs": 0,
        "cur_batch": 0,
        "request_pending": False,
        "latest_message": "",
        "history_messages": []
    })
    
    async def get_pipeline_status_lock(self):
        return self._pipeline_status_lock
    
    async def get_pipeline_status(self):
        return self._pipeline_status
```

**修改** `aperag/graph/lightrag/lightrag.py`:
```python
# 在 __post_init__ 中
def __post_init__(self):
    # 创建实例级状态管理器
    self._state_manager = InstanceStateManager(workspace=self.workspace)
    
    # 不再调用全局的 initialize_share_data()
    # initialize_share_data()  # 删除这行
```

#### 步骤2：修复事件循环管理（Week 1）

**创建新文件** `aperag/graph/lightrag/event_loop_manager.py`:
```python
import asyncio
from typing import Optional, Callable

class EventLoopManager:
    """管理事件循环，避免与Celery冲突"""
    
    @staticmethod
    def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
        """获取事件循环，但不创建新的"""
        try:
            loop = asyncio.get_running_loop()
            return loop
        except RuntimeError:
            # 仅在没有运行中的循环时返回当前循环
            return asyncio.get_event_loop()
    
    @staticmethod
    async def run_async_initialization(async_func: Callable):
        """同步等待异步初始化完成"""
        await async_func()
```

**修改** `aperag/graph/lightrag/lightrag.py` 的初始化：
```python
def __post_init__(self):
    # ... 其他初始化代码 ...
    
    # 修复：同步等待存储初始化
    if self.auto_manage_storages_states:
        # 使用同步方式确保初始化完成
        loop = EventLoopManager.get_or_create_event_loop()
        if loop.is_running():
            # 在异步环境中，创建任务并立即等待
            async def init_wrapper():
                await self.initialize_storages()
            
            # 创建 Future 来同步等待
            future = asyncio.ensure_future(init_wrapper())
            # 这里不能使用 run_until_complete，需要特殊处理
            self._init_future = future
        else:
            # 在同步环境中，直接运行
            loop.run_until_complete(self.initialize_storages())
```

#### 步骤3：改造文档处理流程（Week 2）

**修改** `aperag/graph/lightrag/lightrag.py` 的 `apipeline_process_enqueue_documents`:
```python
async def apipeline_process_enqueue_documents(self, ...):
    # 使用实例级状态而不是全局状态
    pipeline_status = self._state_manager._pipeline_status
    pipeline_status_lock = self._state_manager._pipeline_status_lock
    
    async with pipeline_status_lock:
        # 移除全局 busy 检查，改为 collection 级别
        collection_key = f"busy_{self.workspace}"
        
        if not pipeline_status.get(collection_key, False):
            pipeline_status[collection_key] = True
            # 继续处理...
        else:
            # 对于同一 collection 的并发请求，仍然排队
            pipeline_status[f"request_pending_{self.workspace}"] = True
            return
```

### 1.3 Celery集成方案

#### 创建Celery任务包装器
**新建文件** `aperag/tasks/lightrag_wrapper.py`:
```python
import asyncio
from typing import List, Optional
from celery import Task
from aperag.graph.lightrag import LightRAG

class LightRAGTask(Task):
    """Celery任务基类，处理LightRAG实例管理"""
    
    _instances: dict[str, LightRAG] = {}
    _locks: dict[str, asyncio.Lock] = {}
    
    def get_or_create_instance(self, collection_id: str) -> LightRAG:
        """获取或创建LightRAG实例"""
        if collection_id not in self._instances:
            # 创建新实例时使用独立的事件循环
            instance = LightRAG(
                working_dir=f"./lightrag_cache/{collection_id}",
                workspace=collection_id,
                auto_manage_storages_states=False  # 手动管理初始化
            )
            
            # 在新的事件循环中初始化
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(instance.initialize_storages())
            finally:
                # 清理事件循环，避免影响Celery
                loop.close()
                asyncio.set_event_loop(None)
            
            self._instances[collection_id] = instance
            self._locks[collection_id] = asyncio.Lock()
        
        return self._instances[collection_id]
```

#### 修改现有Celery任务
```python
from aperag.tasks.lightrag_wrapper import LightRAGTask

@app.task(base=LightRAGTask, bind=True)
def process_documents_task(
    self, 
    documents: List[str], 
    collection_id: str
):
    """处理文档的Celery任务"""
    # 获取实例
    rag = self.get_or_create_instance(collection_id)
    
    # 创建新的事件循环执行异步操作
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 使用实例级锁确保同一collection的串行处理
        async def process():
            async with self._locks[collection_id]:
                await rag.ainsert(documents)
        
        loop.run_until_complete(process())
        return {"status": "success", "collection_id": collection_id}
    
    except Exception as e:
        return {"status": "error", "error": str(e)}
    
    finally:
        loop.close()
        asyncio.set_event_loop(None)
```

### 1.4 测试计划

#### 单元测试
```python
# tests/test_concurrent_lightrag.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_multiple_instances():
    """测试多个LightRAG实例可以并发处理不同collection"""
    rag1 = LightRAG(workspace="collection1")
    rag2 = LightRAG(workspace="collection2")
    
    # 并发插入
    results = await asyncio.gather(
        rag1.ainsert(["doc1"]),
        rag2.ainsert(["doc2"])
    )
    
    assert all(r is not None for r in results)

@pytest.mark.asyncio  
async def test_celery_integration():
    """测试Celery任务可以正确处理文档"""
    from aperag.tasks import process_documents_task
    
    result = process_documents_task.delay(
        ["test doc"], 
        "test_collection"
    ).get()
    
    assert result["status"] == "success"
```

### 1.5 实施步骤

1. **Week 1**: 
   - 实现InstanceStateManager
   - 修复事件循环管理
   - 创建测试用例

2. **Week 2**:
   - 改造文档处理流程
   - 实现Celery任务包装器
   - 集成测试

3. **Week 3**:
   - 性能测试和优化
   - 文档更新
   - 部署验证

### 1.6 向后兼容性保证

1. **API兼容**：所有公开API保持不变
2. **配置兼容**：现有配置继续工作
3. **渐进迁移**：提供迁移指南和工具

## 第二阶段：状态管理改造（逐步移除全局状态）

### 2.1 创建实例级状态管理器
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

### 2.2 重构全局锁机制
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

已经用workspace参数实现，所有的数据库都用workspace隔离collection的数据。

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

