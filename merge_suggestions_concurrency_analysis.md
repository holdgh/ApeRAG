# Merge Suggestions 接口并发问题分析报告

## 问题描述

在 `/collections/{collection_id}/graphs/merge-suggestions` 接口处理同一个 collection 时，期望会先删除之前的数据，但在 `graph_index_merge_suggestions` 表中发现同一个 collection 有不同的 `batch_id` 数据，怀疑是并发调用导致的重复写入。

## 代码分析

### 1. 接口流程分析

基于对代码的分析，当前的处理流程如下：

```
1. 接收请求 -> merge_suggestions_view() 
2. 调用 graph_service.get_or_generate_merge_suggestions()
3. 检查缓存 (if not force_refresh)
4. 如果有缓存，返回缓存结果
5. 如果无缓存，生成新建议
6. 如果 force_refresh=True，删除旧数据
7. 批量创建新建议
```

### 2. 并发问题根本原因

#### 2.1 缺乏原子性操作

关键问题在于 **缓存检查** 和 **数据创建** 之间不是原子操作：

```python
# 第一步：检查缓存 (lines 163-167 in graph_service.py)
if not force_refresh:
    cached_suggestions = await self.db_ops.get_valid_suggestions(collection_id)
    if cached_suggestions:
        return self._format_suggestions_response(cached_suggestions, from_cache=True)

# 第二步：生成新建议 (lines 169-182)
llm_result = await self.generate_merge_suggestions(...)

# 第三步：存储新建议 (lines 184-198)
if suggestion_data:
    if force_refresh:  # 只有在 force_refresh=True 时才删除
        deleted_count = await self.db_ops.delete_all_suggestions_for_collection(collection_id)
    
    stored_suggestions = await self.db_ops.batch_create_suggestions(suggestion_data)
```

#### 2.2 并发场景分析

**场景：两个并发请求处理同一个 collection，且 force_refresh=False**

```
时间线：
T1: 请求A检查缓存 -> 无缓存
T2: 请求B检查缓存 -> 无缓存  
T3: 请求A开始生成LLM建议
T4: 请求B开始生成LLM建议
T5: 请求A完成LLM生成，开始存储 (batch_id=batch123)
T6: 请求B完成LLM生成，开始存储 (batch_id=batch456)
T7: 两个请求都成功存储，导致重复数据
```

#### 2.3 数据库约束无法阻止此问题

数据库的唯一约束是：
```python
UniqueConstraint("collection_id", "entity_ids_hash", "gmt_deleted", name="uq_graph_index_merge_suggestion")
```

这个约束只能防止 **相同实体组合** 的重复，但无法防止：
1. 不同 batch_id 的数据共存
2. 并发请求生成不同的实体组合建议

### 3. 问题影响

1. **数据冗余**：同一 collection 存在多个 batch 的建议数据
2. **用户体验差**：可能显示重复或冲突的合并建议
3. **资源浪费**：重复的 LLM 调用和数据存储

### 4. 解决方案建议

#### 4.1 分布式锁方案 (推荐)
```python
async def get_or_generate_merge_suggestions(self, ...):
    lock_key = f"merge_suggestions:{collection_id}"
    async with distributed_lock(lock_key, timeout=300):  # 5分钟超时
        # 原有逻辑
        if not force_refresh:
            cached_suggestions = await self.db_ops.get_valid_suggestions(collection_id)
            if cached_suggestions:
                return self._format_suggestions_response(cached_suggestions, from_cache=True)
        
        # 生成和存储逻辑...
```

#### 4.2 数据库级别的原子操作
```python
async def get_or_generate_merge_suggestions_atomic(self, ...):
    # 在事务中先尝试获取锁记录
    # 如果获取成功，继续处理
    # 如果获取失败，等待或返回现有结果
```

#### 4.3 幂等性处理
```python
# 在 force_refresh=False 时也检查并清理旧数据
if suggestion_data:
    # 无论 force_refresh 值，都先删除旧数据
    deleted_count = await self.db_ops.delete_all_suggestions_for_collection(collection_id)
    stored_suggestions = await self.db_ops.batch_create_suggestions(suggestion_data)
```

#### 4.4 任务队列方案
将建议生成改为异步任务，避免重复提交。

## 总结

问题的根本原因是 **缺乏并发控制机制**，导致多个请求可以同时通过缓存检查并生成新的建议数据。建议采用分布式锁或数据库级别的原子操作来解决此问题。