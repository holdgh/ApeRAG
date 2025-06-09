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
