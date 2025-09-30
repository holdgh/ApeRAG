"""
Celery Task System for Document Indexing - Dynamic Workflow Architecture

This module implements a dynamic task system for document indexing with runtime workflow orchestration.
All tasks use structured data classes for parameter passing and result handling.

## Architecture Overview

The new task system is designed with the following principles:
1. **Fine-grained tasks**: Each operation (parse, create index, delete index, update index) is a separate task
2. **Dynamic workflow orchestration**: Tasks are composed at runtime using trigger tasks
3. **Parallel execution**: Index creation/update/deletion tasks run in parallel for better performance
4. **Individual retries**: Each task has its own retry mechanism with configurable parameters
5. **Runtime decision making**: Workflows can adapt based on document content and parsing results

## Task Flow Architecture

### Sequential Phase (Chain):
```
parse_document_task -> trigger_indexing_workflow
```

### Parallel Phase (Group + Chord):
```
[create_index_task(vector), create_index_task(fulltext), create_index_task(graph)] -> notify_workflow_complete
```

### Key Innovation: Dynamic Fan-out
The `trigger_indexing_workflow` task receives parsed document data and dynamically creates
the parallel index tasks, solving the static parameter passing limitation.

## Task Hierarchy

### Core Tasks:
- `parse_document_task`: Parse document content and extract metadata
- `create_index_task`: Create a single type of index (vector/fulltext/graph)
- `delete_index_task`: Delete a single type of index
- `update_index_task`: Update a single type of index

### Workflow Orchestration Tasks:
- `trigger_create_indexes_workflow`: Dynamic fan-out for index creation
- `trigger_delete_indexes_workflow`: Dynamic fan-out for index deletion
- `trigger_update_indexes_workflow`: Dynamic fan-out for index updates
- `notify_workflow_complete`: Aggregation task for workflow completion

### Workflow Entry Points:
- `create_document_indexes_workflow()`: Chain composition function
- `delete_document_indexes_workflow()`: Chain composition function
- `update_document_indexes_workflow()`: Chain composition function

## Usage Examples

### Direct Workflow Execution:
```python
from config.celery_tasks import create_document_indexes_workflow

# Execute workflow with dynamic orchestration
workflow_result = create_document_indexes_workflow(
    document_id="doc_123",
    index_types=["vector", "fulltext", "graph"]
)

print(f"Workflow ID: {workflow_result.id}")
```

### Via TaskScheduler:
```python
from aperag.tasks.scheduler import create_task_scheduler

scheduler = create_task_scheduler("celery")

# Execute workflow via scheduler
workflow_id = scheduler.schedule_create_index(
    document_id="doc_123",
    index_types=["vector", "fulltext"]
)

# Check status
status = scheduler.get_task_status(workflow_id)
print(f"Success: {status.success}")
```

## Benefits of Dynamic Orchestration

1. **Runtime Parameter Passing**: Index tasks receive actual parsed document data
2. **Adaptive Workflows**: Can decide which indexes to create based on document content
3. **Better Error Isolation**: Parse failures don't create orphaned index tasks
4. **Clear Data Flow**: Each task knows exactly what data it will receive
5. **Extensible**: Easy to add conditional logic for different document types

## Error Handling and Retries

Each task has built-in retry mechanisms:
- **Max retries**: 3 attempts for most tasks
- **Retry countdown**: 60 seconds between retries
- **Exception handling**: Detailed logging and error callbacks
- **Failure notifications**: Integration with index_task_callbacks for status updates
"""

import json
import logging
from contextlib import asynccontextmanager
from typing import Any, List

from celery import Task, chain, chord, current_app, group

from aperag.tasks.collection import collection_task
from aperag.tasks.document import document_index_task
from aperag.tasks.models import (
    IndexTaskResult,
    ParsedDocumentData,
    TaskStatus,
    WorkflowResult,
)
from aperag.tasks.utils import TaskConfig
from aperag.utils.constant import IndexAction
from config.celery_app import app

logger = logging.getLogger()

def _validate_task_relevance(document_id: str, index_type: str, target_version: int, expected_status: "DocumentIndexStatus"):  # 对于新增/更新类索引任务，校验其任务有效性
    """
    Double-check the database to ensure the task is still valid.

    Returns a dictionary with a 'skipped' status if the task is no longer relevant,
    otherwise returns None.
    """
    from aperag.db.models import DocumentIndex, DocumentIndexType, Document, DocumentStatus
    from aperag.aperag_config import get_sync_session
    from sqlalchemy import select, and_

    for session in get_sync_session():
        # -- 基于文档id和索引类型查询文档索引任务记录
        # Check document index status
        stmt = select(DocumentIndex).where(
            and_(
                DocumentIndex.document_id == document_id,
                DocumentIndex.index_type == DocumentIndexType(index_type)
            )
        )
        result = session.execute(stmt)
        db_index = result.scalar_one_or_none()
        # -- 基于查询的文档索引任务记录进行第一次有效性验证
        if not db_index:  # 索引任务不存在
            logger.info(f"Index record not found for {document_id}:{index_type}, skipping task.")
            return {"status": "skipped", "reason": "index_record_not_found"}

        if db_index.status != expected_status:  # 索引任务状态与预期【新增/更新类索引任务--DocumentIndexStatus.CREATING】不符
            logger.info(f"Index status for {document_id}:{index_type} changed to {db_index.status} (expected {expected_status}), skipping task.")
            return {"status": "skipped", "reason": f"status_changed_to_{db_index.status}"}

        if target_version and db_index.version != target_version:  # 索引任务最新版本号与当前异步任务处理上下文中的版本号【这个参数也是从数据库查询的，但是整个异步任务处理逻辑执行到此会经历一段时间【可能有其他操作更新了索引任务，版本号也随即更新了，乐观锁的逻辑】，这里做状态一致性核验】不符
            logger.info(f"Version mismatch for {document_id}:{index_type}, expected: {target_version}, current: {db_index.version}, skipping task.")
            return {"status": "skipped", "reason": f"version_mismatch_expected_{target_version}_current_{db_index.version}"}
        # -- 基于文档id查询文档记录
        # Check document status - if document is UPLOADED or EXPIRED, task should be skipped
        doc_stmt = select(Document).where(Document.id == document_id)
        doc_result = session.execute(doc_stmt)
        document = doc_result.scalar_one_or_none()
        # -- 基于查询的文档记录进行第二次有效性验证
        if not document:  # 文档不存在
            logger.info(f"Document {document_id} not found, skipping task.")
            return {"status": "skipped", "reason": "document_not_found"}

        if document.status in [DocumentStatus.UPLOADED, DocumentStatus.EXPIRED]:  # 文档状态为DocumentStatus.UPLOADED或DocumentStatus.EXPIRED
            logger.info(f"Document {document_id} status is {document.status}, skipping task.")
            return {"status": "skipped", "reason": f"document_status_{document.status}"}
        # 上述双重核验通过，当前索引任务可执行
        return None  # Task is still relevant

class BaseIndexTask(Task):  # 对于所有索引任务的基类定义
    """
    Base class for all index tasks
    """

    abstract = True

    def _handle_index_success(self, document_id: str, index_type: str, target_version: int, index_data: dict = None):  # 处理新增/修改索引任务成功时的回调操作【标记索引任务为ACTIVE，并更新原始文件状态】
        try:
            from aperag.tasks.reconciler import index_task_callbacks
            index_data_json = json.dumps(index_data) if index_data else None
            index_task_callbacks.on_index_created(document_id, index_type, target_version, index_data_json)  # 更新索引任务状态，然后根据索引任务状态更新文档状态
            logger.info(f"Index success callback executed for {index_type} index of document {document_id} (v{target_version})")
        except Exception as e:
            logger.warning(f"Failed to execute index success callback for {index_type} of {document_id} v{target_version}: {e}", exc_info=True)

    def _handle_index_deletion_success(self, document_id: str, index_type: str):  # 处理删除索引任务成功时的回调操作
        try:
            from aperag.tasks.reconciler import index_task_callbacks
            index_task_callbacks.on_index_deleted(document_id, index_type)
            logger.info(f"Index deletion callback executed for {index_type} index of document {document_id}")
        except Exception as e:
            logger.warning(f"Failed to execute index deletion callback for {index_type} of {document_id}: {e}", exc_info=True)

    def _handle_index_failure(self, document_id: str, index_types: List[str], error_msg: str):  # 索引任务处理失败的回调操作【标记索引任务为FAILED，并更新原始文件状态】
        try:
            from aperag.tasks.reconciler import index_task_callbacks

            for index_type in index_types:
                index_task_callbacks.on_index_failed(document_id, index_type, error_msg)
            logger.info(f"Index failure callback executed for {index_types} indexes of document {document_id}")
        except Exception as e:
            logger.warning(f"Failed to execute index failure callback for {document_id}: {e}", exc_info=True)

# ========== Core Document Processing Tasks ==========

@current_app.task(bind=True, base=BaseIndexTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def parse_document_task(self, document_id: str, index_types: List[str]) -> dict:  # 解析文档【字典形式返回：知识库及文件信息、文件解析结果【markdown文件内容、非视觉资源实例列表】、本地原始文件信息【本地路径、是否为临时文件】】，最大重试次数为3次，
    """
    Parse document content task

    Args:
        document_id: Document ID to parse

    Returns:
        Serialized ParsedDocumentData
    """
    try:
        logger.info(f"Starting to parse document {document_id}")
        parsed_data = document_index_task.parse_document(document_id)
        logger.info(f"Successfully parsed document {document_id}")
        return parsed_data.to_dict()  # 将文档解析数据转化为字典，包括：知识库及文件信息、文件解析结果【markdown文件内容、非视觉资源实例列表】、本地原始文件信息【本地路径、是否为临时文件】
    except Exception as e:
        error_msg = f"Failed to parse document {document_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Only mark as failed if all retries are exhausted
        if self.request.retries >= self.max_retries:
            self._handle_index_failure(document_id, index_types, error_msg)  # 索引任务失败回调

        raise


@current_app.task(bind=True, base=BaseIndexTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def create_index_task(self, document_id: str, index_type: str, parsed_data_dict: dict, context: dict = None) -> dict:  # 对于单个文档的特定索引类型，基于文档解析结果，执行创建索引操作
    """
    Create a single index for a document with distributed locking

    Args:
        document_id: Document ID to process
        index_type: Type of index to create ('vector', 'fulltext', 'graph')
        parsed_data_dict: Serialized ParsedDocumentData from parse_document_task【字典形式：知识库及文件信息、文件解析结果【markdown文件内容、非视觉资源实例列表】、本地原始文件信息【本地路径、是否为临时文件】】
        context: Task context including index version  当前文档索引任务记录的最新版本号，形如“context[f"{index_type}_version"] = target_version”

    Returns:
        Serialized IndexTaskResult
    """
    from aperag.db.models import DocumentIndex, DocumentIndexType, DocumentIndexStatus
    from aperag.aperag_config import get_sync_session
    from sqlalchemy import select, and_
    # -- 获取入参中的当前文档索引任务记录的最新版本号
    # Extract target version from context
    context = context or {}
    target_version = context.get(f'{index_type}_version')  # 获取当前文档索引任务记录的最新版本号

    try:
        logger.info(f"Starting to create {index_type} index for document {document_id} (v{target_version})")
        # -- 验证当前任务是否有效【双重验证：基于文档索引任务记录和文档记录的有效性验证】
        # Double-check: verify task is still valid
        skip_reason = _validate_task_relevance(document_id, index_type, target_version, DocumentIndexStatus.CREATING)
        if skip_reason:  # 无效原因非空，则直接返回无效原因
            return skip_reason
        # -- 将文档解析结果字典形式转化为ParsedDocumentData实例
        # Convert dict back to structured data
        parsed_data = ParsedDocumentData.from_dict(parsed_data_dict)
        # -- 基于文档解析结果和索引类型，执行创建索引
        # Execute index creation
        result = document_index_task.create_index(document_id, index_type, parsed_data)
        # -- 检查创建索引是否成功【失败则触发重试机制【3次，见方法头部注解】】
        # Check if the operation failed and raise exception to trigger retry
        if not result.success:
            error_msg = f"Failed to create {index_type} index for document {document_id}: {result.error}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Handle success callback with version validation
        logger.info(f"Successfully created {index_type} index for document {document_id} (v{target_version})")
        self._handle_index_success(document_id, index_type, target_version, result.data)  # 标记索引任务为ACTIVE，并更新原始文件状态

        return result.to_dict()

    except Exception as e:
        error_msg = f"Failed to create {index_type} index for document {document_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Only mark as failed if all retries are exhausted
        if self.request.retries >= self.max_retries:
            self._handle_index_failure(document_id, [index_type], error_msg)

        raise


@current_app.task(bind=True, base=BaseIndexTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def delete_index_task(self, document_id: str, index_type: str) -> dict:
    """
    Delete a single index for a document

    Args:
        document_id: Document ID to process
        index_type: Type of index to delete ('vector', 'fulltext', 'graph')

    Returns:
        Serialized IndexTaskResult
    """
    from aperag.db.models import DocumentIndex, DocumentIndexType, DocumentIndexStatus
    from aperag.aperag_config import get_sync_session
    from sqlalchemy import select, and_

    try:
        logger.info(f"Starting to delete {index_type} index for document {document_id}")

        # Double-check: verify task is still valid
        for session in get_sync_session():
            stmt = select(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType(index_type)
                )
            )
            result = session.execute(stmt)
            db_index = result.scalar_one_or_none()

            # Validate task is still relevant
            if not db_index:
                logger.info(f"Index record not found for {document_id}:{index_type}, already deleted")
                return {"status": "skipped", "reason": "index_record_not_found"}

            if db_index.status != DocumentIndexStatus.DELETION_IN_PROGRESS:
                logger.info(f"Index status changed for {document_id}:{index_type}, current: {db_index.status}, skipping task")
                return {"status": "skipped", "reason": f"status_changed_to_{db_index.status}"}

            break

        # Execute index deletion
        result = document_index_task.delete_index(document_id, index_type)

        # Check if the operation failed and raise exception to trigger retry
        if not result.success:
            error_msg = f"Failed to delete {index_type} index for document {document_id}: {result.error}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Handle success callback
        logger.info(f"Successfully deleted {index_type} index for document {document_id}")
        self._handle_index_deletion_success(document_id, index_type)

        return result.to_dict()

    except Exception as e:
        error_msg = f"Failed to delete {index_type} index for document {document_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Only mark as failed if all retries are exhausted
        if self.request.retries >= self.max_retries:
            self._handle_index_failure(document_id, [index_type], error_msg)

        raise


@current_app.task(bind=True, base=BaseIndexTask, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def update_index_task(self, document_id: str, index_type: str, parsed_data_dict: dict, context: dict = None) -> dict:
    """
    Update a single index for a document with distributed locking

    Args:
        document_id: Document ID to process
        index_type: Type of index to update ('vector', 'fulltext', 'graph')
        parsed_data_dict: Serialized ParsedDocumentData from parse_document_task
        context: Task context including index version

    Returns:
        Serialized IndexTaskResult
    """
    from aperag.db.models import DocumentIndex, DocumentIndexType, DocumentIndexStatus
    from aperag.aperag_config import get_sync_session
    from sqlalchemy import select, and_

    # Extract target version from context
    context = context or {}
    target_version = context.get(f'{index_type}_version')

    try:
        logger.info(f"Starting to update {index_type} index for document {document_id} (v{target_version})")

        # Double-check: verify task is still valid
        skip_reason = _validate_task_relevance(document_id, index_type, target_version, DocumentIndexStatus.CREATING)
        if skip_reason:
            return skip_reason

        # Convert dict back to structured data
        parsed_data = ParsedDocumentData.from_dict(parsed_data_dict)

        # Execute index update
        result = document_index_task.update_index(document_id, index_type, parsed_data)  # 更新index_type类型的索引

        # Check if the operation failed and raise exception to trigger retry
        if not result.success:
            error_msg = f"Failed to update {index_type} index for document {document_id}: {result.error}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Handle success callback with version validation
        logger.info(f"Successfully updated {index_type} index for document {document_id} (v{target_version})")
        self._handle_index_success(document_id, index_type, target_version, result.data)

        return result.to_dict()

    except Exception as e:
        error_msg = f"Failed to update {index_type} index for document {document_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Only mark as failed if all retries are exhausted
        if self.request.retries >= self.max_retries:
            self._handle_index_failure(document_id, [index_type], error_msg)

        raise


# ========== Dynamic Workflow Orchestration Tasks ==========

@current_app.task(bind=True)
def trigger_create_indexes_workflow(self, parsed_data_dict: dict, document_id: str, index_types: List[str], context: dict = None) -> Any:  # 触发创建索引工作流。
    """
    参数说明：
    parsed_data_dict参数是解析文档结果，见aperag.tasks.document.DocumentIndexTask.parse_document和aperag.tasks.models.ParsedDocumentData.to_dict
    context参数为文档索引任务记录的最新版本号，形如“context[f"{index_type}_version"] = target_version”
    """
    """
    Dynamic orchestration task for index creation workflow.

    This task acts as a fan-out point, receiving parsed document data and dynamically
    creating parallel index creation tasks based on the actual parsed content.

    Args:
        parsed_data_dict: Serialized ParsedDocumentData from parse_document_task 解析结果包含：知识库及文件信息、文件解析结果【markdown文件内容、非视觉资源实例列表】、本地原始文件信息【本地路径、是否为临时文件】
        document_id: Document ID to process
        index_types: List of index types to create

    Returns:
        Chord signature for parallel index creation + completion notification
    """
    try:
        logger.info(f"Triggering parallel index creation for document {document_id} with types: {index_types}")
        """
        group和chord代码的核心逻辑是 **“基于组索引类型创建并行任务，并在所有任务完成后触发通知”**，利用 Celery 的 `group` 和 `chord` 实现了“并行执行 + 完成回调”的工作流。下面分步骤详细解析：
        
        
        ### 1. 核心组件说明
        在分析代码前，先明确两个关键工具（均为 Celery 提供的任务编排工具）：
        - **`group`**：用于创建**并行任务组**，可以将多个任务同时提交执行，提高效率；
        - **`chord`**：用于创建**“并行任务组 + 回调任务”** 的组合，确保所有并行任务完成后，自动执行一个“收尾”的回调任务。
        
        
        ### 2. 代码逻辑拆解
        
        #### 步骤1：创建并行索引任务组（`parallel_index_tasks`）
        ```python
        parallel_index_tasks = group([
            create_index_task.s(document_id, index_type, parsed_data_dict, context)
            for index_type in index_types
        ])
        ```
        - **作用**：根据传入的 `index_types`（索引类型列表，如 `["fulltext", "vector", "keyword"]`），为每种索引类型创建一个 `create_index_task` 任务，并将这些任务组合成一个**并行执行的任务组**。
        - **细节**：
          - `create_index_task.s(...)` 是任务签名（`signature`），表示“准备执行 `create_index_task` 任务，参数为 `document_id, index_type, parsed_data_dict, context`”；
          - 列表推导式 `for index_type in index_types` 会遍历所有索引类型，为每个类型生成一个独立的任务；
          - `group(...)` 将这些任务打包，形成一个“并行任务组”，执行时所有任务会同时启动（而非串行等待）。
        
        
        #### 步骤2：创建带回调的任务链（`workflow_chord`）
        ```python
        workflow_chord = chord(
            parallel_index_tasks,  # 并行任务组（第一个参数）
            notify_workflow_complete.s(document_id, IndexAction.CREATE, index_types)  # 回调任务（第二个参数）
        )
        ```
        - **作用**：定义一个“先并行执行任务组，再执行回调任务”的工作流。
        - **细节**：
          - 第一个参数 `parallel_index_tasks` 是步骤1创建的并行任务组，会先执行；
          - 第二个参数 `notify_workflow_complete.s(...)` 是回调任务签名，表示“当所有并行任务完成后，执行 `notify_workflow_complete` 任务”；
          - 回调任务的参数为 `document_id, IndexAction.CREATE, index_types`，用于通知“文档ID为 `document_id` 的索引创建操作（`CREATE`）已完成，涉及的索引类型是 `index_types`”。
        
        
        #### 步骤3：执行工作流并返回结果
        ```python
        workflow_chord.apply_async()  # 异步执行整个工作流
        return workflow_chord  # 返回工作流对象（可用于跟踪状态）
        ```
        - **`apply_async()`**：触发整个工作流的异步执行（非阻塞，立即返回），所有并行任务会被提交到 Celery  worker 执行；
        - **返回 `workflow_chord`**：调用方可以通过这个对象跟踪工作流状态（如是否完成、是否失败）。
        
        
        ### 3. 执行流程时序图
        整个工作流的执行顺序如下：
        ```
        开始
          │
          ├─ 对 index_types 中的每个类型，并行执行 create_index_task：
          │  ├─ create_index_task(document_id, "类型1", parsed_data_dict, context)
          │  ├─ create_index_task(document_id, "类型2", parsed_data_dict, context)
          │  └─ ...（更多类型）
          │
          ├─ 等待所有并行任务完成（成功或失败）
          │
          └─ 执行回调任务：
             └─ notify_workflow_complete(document_id, IndexAction.CREATE, index_types)
        结束
        ```
        
        
        ### 4. 核心价值
        这段代码通过 `group` 和 `chord` 实现了两个关键能力：
        1. **并行效率**：不同类型的索引创建任务同时执行，减少总体耗时（例如，创建全文索引和向量索引可以并行，无需等待一个完成再开始另一个）；
        2. **状态闭环**：确保所有索引任务完成后，通过 `notify_workflow_complete` 发送通知（如更新文档状态、通知用户等），避免“任务执行后无反馈”的问题。
        
        
        ### 总结
        这段代码是一个典型的“并行任务 + 回调”工作流实现：
        - 用 `group` 将同类型的索引创建任务并行化，提高处理效率；
        - 用 `chord` 确保所有并行任务完成后触发回调，实现工作流的闭环；
        - 整体逻辑清晰，适合“多任务并行处理，最后统一收尾”的场景（如批量创建不同类型的索引、批量处理文件后通知结果等）。
        """
        # -- 基于索引类型列表，创建并行索引任务组【对于单个文档的特定索引类型，基于文档解析结果【字典形式：知识库及文件信息、文件解析结果【markdown文件内容、非视觉资源实例列表】、本地原始文件信息【本地路径、是否为临时文件】】，执行创建索引】
        # Dynamically create parallel index creation tasks
        parallel_index_tasks = group([
            create_index_task.s(document_id, index_type, parsed_data_dict, context)
            for index_type in index_types
        ])  # 形成一个“并行任务组”，执行时所有任务会同时启动（而非串行等待）

        # Create a chord that executes the completion notification after all create tasks are done
        workflow_chord = chord(
            parallel_index_tasks,  # 并行任务组（第一个参数）
            notify_workflow_complete.s(document_id, IndexAction.CREATE, index_types)  # 回调任务（第二个参数）
        )  # 先并行执行任务组，再执行回调任务。触发整个工作流的异步执行（非阻塞，立即返回），所有并行任务会被提交到 Celery  worker 执行；

        # Execute the chord
        workflow_chord.apply_async()  # 异步执行整个工作流

        return workflow_chord  # 调用方可以通过这个对象跟踪工作流状态（如是否完成、是否失败）。

    except Exception as e:
        error_msg = f"Failed to trigger create indexes workflow: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise


@current_app.task(bind=True)
def trigger_delete_indexes_workflow(self, document_id: str, index_types: List[str]) -> Any:
    """
    Dynamic orchestration task for index deletion workflow.

    Args:
        document_id: Document ID to process
        index_types: List of index types to delete

    Returns:
        Chord signature for parallel index deletion + completion notification
    """
    try:
        logger.info(f"Triggering parallel index deletion for document {document_id} with types: {index_types}")

        # Create parallel index deletion tasks
        parallel_delete_tasks = group([
            delete_index_task.s(document_id, index_type)
            for index_type in index_types
        ])

        # Create a chord that executes the completion notification after all delete tasks are done
        workflow_chord = chord(
            parallel_delete_tasks,
            notify_workflow_complete.s(document_id, IndexAction.DELETE, index_types)
        )

        # Execute the chord
        workflow_chord.apply_async()

        return workflow_chord

    except Exception as e:
        error_msg = f"Failed to trigger delete indexes workflow: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise


@current_app.task(bind=True)
def trigger_update_indexes_workflow(self, parsed_data_dict: dict, document_id: str, index_types: List[str], context: dict = None) -> Any:
    """
    Dynamic orchestration task for index update workflow.

    Args:
        parsed_data_dict: Serialized ParsedDocumentData from parse_document_task
        document_id: Document ID to process
        index_types: List of index types to update

    Returns:
        Chord signature for parallel index update + completion notification
    """
    try:
        logger.info(f"Triggering parallel index update for document {document_id} with types: {index_types}")

        # Create parallel index update tasks
        parallel_update_tasks = group([
            update_index_task.s(document_id, index_type, parsed_data_dict, context)
            for index_type in index_types
        ])

        # Create chord: parallel tasks + completion notification
        workflow_chord = chord(
            parallel_update_tasks,
            notify_workflow_complete.s(document_id, IndexAction.UPDATE, index_types)
        )

        chord_async_result = workflow_chord.apply_async()

        return chord_async_result

    except Exception as e:
        error_msg = f"Failed to trigger update indexes workflow: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise


@current_app.task(bind=True, base=BaseIndexTask)
def notify_workflow_complete(self, index_results: List[dict], document_id: str, operation: str, index_types: List[str]) -> dict:  # 在所有并行索引任务执行完毕后，汇总结果
    """
    Workflow completion notification task.

    This task is called after all parallel index operations complete,
    aggregating results and providing final workflow status.

    Args:
        index_results: List of IndexTaskResult dicts from parallel tasks
        document_id: Document ID that was processed
        operation: Operation type ('create', 'delete', 'update')
        index_types: List of index types that were processed

    Returns:
        Serialized WorkflowResult
    """
    try:
        logger.info(f"Workflow {operation} completed for document {document_id}")
        logger.info(f"Index results: {index_results}")
        # 收集索引任务是否执行成功
        # Analyze results
        successful_tasks = []
        failed_tasks = []

        for result_dict in index_results:
            try:
                result = IndexTaskResult.from_dict(result_dict)
                if result.success:
                    successful_tasks.append(result.index_type)
                else:
                    failed_tasks.append(f"{result.index_type}: {result.error}")
            except Exception as e:
                failed_tasks.append(f"unknown: {str(e)}")
        # 打印索引任务执行情况【哪个文档的哪类任务执行成功/失败】
        # Determine overall status
        if not failed_tasks:
            status = TaskStatus.SUCCESS
            status_message = f"Document {document_id} {operation} COMPLETED SUCCESSFULLY! All indexes processed: {', '.join(successful_tasks)}"
            logger.info(status_message)
        elif successful_tasks:
            status = TaskStatus.PARTIAL_SUCCESS
            status_message = f"Document {document_id} {operation} COMPLETED with WARNINGS. Success: {', '.join(successful_tasks)}. Failures: {'; '.join(failed_tasks)}"
            logger.warning(status_message)
        else:
            status = TaskStatus.FAILED
            status_message = f"Document {document_id} {operation} FAILED. All tasks failed: {'; '.join(failed_tasks)}"
            logger.error(status_message)
        # 汇总索引结果
        # Create workflow result
        workflow_result = WorkflowResult(
            workflow_id=f"{document_id}_{operation}",  # 工作流标识【文档id_索引任务类型】
            document_id=document_id,
            operation=operation,  # 索引任务类型【创建、更新、删除】
            status=status,  # 当前类索引任务的所有索引类型任务执行状态【全部成功、部分成功、全部失败】
            message=status_message,  # 当前类索引任务的所有索引类型任务执行细节【哪些索引类型成功、哪些索引类型失败】
            successful_indexes=successful_tasks,  # 执行成功的索引类型
            failed_indexes=[f.split(':')[0] for f in failed_tasks], # 执行失败的索引类型
            total_indexes=len(index_types),  # 全量索引类型
            index_results=[IndexTaskResult.from_dict(r) for r in index_results]  # 全量索引任务执行结果明细列表
        )

        return workflow_result.to_dict()

    except Exception as e:
        error_msg = f"Failed to process workflow completion for document {document_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Return failure result
        workflow_result = WorkflowResult(
            workflow_id=f"{document_id}_{operation}",
            document_id=document_id,
            operation=operation,
            status=TaskStatus.FAILED,
            message=error_msg,
            successful_indexes=[],
            failed_indexes=index_types,
            total_indexes=len(index_types),
            index_results=[]
        )

        return workflow_result.to_dict()


# ========== Workflow Entry Point Functions ==========

def create_document_indexes_workflow(document_id: str, index_types: List[str], context: dict = None):  # 对于单个文档，处理创建类索引任务工作流，注意context为文档索引任务记录的最新版本号，形如“context[f"{index_type}_version"] = target_version”
    """
    Create indexes for a document using dynamic workflow orchestration.

    This function composes a chain that:
    1. Parses the document
    2. Dynamically triggers parallel index creation based on parsed content
    3. Aggregates results and notifies completion

    Args:
        document_id: Document ID to process
        index_types: List of index types to create

    Returns:
        AsyncResult for the workflow chain
    """
    logger.info(f"Starting create indexes workflow for document {document_id} with types: {index_types}")
    # -- 创建类索引任务的处理步骤：解析文档-->索引操作
    # Create the workflow chain: parse -> dynamic trigger
    """
    在下述定义的 `workflow_chain` 工作流中，**第一步 `parse_document_task` 的返回结果（字典，含 `content` 字段）会自动作为第二步 `trigger_create_indexes_workflow` 的第一个额外参数被引用**。这是 Celery 中 `chain`（任务链）的核心特性——**前一个任务的返回值会自动传递给后一个任务**，实现任务间的“数据流转”。
        
        ### 具体逻辑拆解
        要理解这一过程，需要结合 Celery `chain` 的工作机制和任务定义（`s()` 是 `signature` 的简写，用于创建任务签名）：
        
        #### 1. 第一步任务：`parse_document_task.s(document_id, index_types)`
        - 任务接收两个显式参数：`document_id`（文档ID）、`index_types`（索引类型）；
        - 执行完成后，返回一个 **字典**（含 `content` 字段，以及知识库信息、文件解析结果等）——这个字典就是“任务返回值”，会被 `chain` 自动暂存。
        
        
        #### 2. 第二步任务：`trigger_create_indexes_workflow.s(document_id, index_types, context)`
        - 任务显式定义了三个参数：`document_id`、`index_types`、`context`；
        - 但在 `chain` 中，**前一个任务（第一步）的返回值会被自动插入到第二步任务的“参数列表最前面”**。  
          也就是说，第二步实际接收的参数顺序是：  
          `(第一步返回的字典, document_id, index_types, context)`。
        
        
        #### 3. 数据引用的关键：第二步任务如何接收第一步结果
        假设 `trigger_create_indexes_workflow` 的函数定义如下（符合 Celery 任务规范）：
        ```python
            @app.task(base=BaseTask)  # 假设继承了基础任务类
            def trigger_create_indexes_workflow(parse_result, document_id, index_types, context):
                # parse_result：就是第一步返回的字典（含 content 字段）
                markdown_content = parse_result.get("content")  # 直接引用第一步的 content 字段
                # 后续逻辑：用 markdown_content 触发索引创建...
                return "索引创建工作流触发成功"
        ```
        可以看到：
        - 第二步任务的 **第一个参数 `parse_result`**，本质就是第一步 `parse_document_task` 返回的字典；
        - 通过 `parse_result["content"]` 或 `parse_result.get("content")`，就能直接引用第一步的 `content` 字段，实现“第一步结果被第二步使用”。
        
        
        ### 为什么会自动传递？—— Celery `chain` 的设计逻辑
        `chain` 是 Celery 为“串行任务”设计的工具，核心目标是**简化任务间的数据依赖**。它的底层逻辑是：
            - 每个任务执行完成后，将返回值存入 Celery 的“结果后端”（如 Redis、RabbitMQ）；
            - 执行下一个任务时，`chain` 会从结果后端读取前一个任务的返回值，自动拼接到下一个任务的参数列表最前面；
            - 最终，下一个任务能通过参数直接拿到前一个任务的结果，无需手动传递或存储。
        
        
        ### 验证：如何确认第一步结果被引用
        如果需要调试或确认数据流转，可在第二步任务中打印参数：
        ```python
        @app.task(base=BaseTask)
        def trigger_create_indexes_workflow(parse_result, document_id, index_types, context):
            print("第一步任务返回的字典：", parse_result)  # 打印第一步结果
            print("第一步的 content 字段：", parse_result.get("content"))  # 打印 content
            # 后续业务逻辑...
        ```
        执行工作流后，通过 Celery 日志（如 `celery -A proj worker --loglevel=info`）可看到第一步返回的字典及 `content` 字段，证明数据已被成功引用。
        
        
        ### 总结
        - **结论**：第一步的返回结果（含 `content` 的字典）会被第二步自动引用，作为第二步的第一个参数传入；
        - **关键**：Celery `chain` 会自动实现“前任务返回值 → 后任务参数”的传递，无需手动处理数据传递逻辑；
        - **使用**：第二步任务只需在函数定义中，将“接收第一步结果的参数”放在参数列表最前面，即可直接使用第一步的 `content` 等字段。
    """
    workflow_chain = chain(
        parse_document_task.s(document_id, index_types),  # 解析文档【字典形式返回：知识库及文件信息、文件解析结果【markdown文件内容、非视觉资源实例列表】、本地原始文件信息【本地路径、是否为临时文件】】
        trigger_create_indexes_workflow.s(document_id, index_types, context)  # 触发创建索引工作流。执行及参数传递说明：第一步解析文档执行完成后，会触发创建索引工作流，并且第一步的结果会作为trigger_create_indexes_workflow的第一个参数
    )

    # Submit the workflow
    workflow_result = workflow_chain.delay()  # 异步执行上述定义的工作流
    logger.info(f"Create indexes workflow submitted for document {document_id}, workflow ID: {workflow_result.id}")

    return workflow_result


def delete_document_indexes_workflow(document_id: str, index_types: List[str]):
    """
    Delete indexes for a document using dynamic workflow orchestration.

    Args:
        document_id: Document ID to process
        index_types: List of index types to delete

    Returns:
        AsyncResult for the workflow
    """
    logger.info(f"Starting delete indexes workflow for document {document_id} with types: {index_types}")

    # For deletion, we don't need parsing, so we directly trigger the delete workflow
    workflow_result = trigger_delete_indexes_workflow.delay(document_id, index_types)
    logger.info(f"Delete indexes workflow submitted for document {document_id}, workflow ID: {workflow_result.id}")

    return workflow_result


def update_document_indexes_workflow(document_id: str, index_types: List[str], context: dict = None):
    """
    Update indexes for a document using dynamic workflow orchestration.

    This function composes a chain that:
    1. Re-parses the document to get updated content
    2. Dynamically triggers parallel index updates based on parsed content
    3. Aggregates results and notifies completion

    Args:
        document_id: Document ID to process
        index_types: List of index types to update

    Returns:
        AsyncResult for the workflow chain
    """
    logger.info(f"Starting update indexes workflow for document {document_id} with types: {index_types}")

    # Create the workflow chain: parse -> dynamic trigger
    workflow_chain = chain(
        parse_document_task.s(document_id, index_types),
        trigger_update_indexes_workflow.s(document_id, index_types, context)
    )

    # Submit the workflow
    workflow_result = workflow_chain.delay()
    logger.info(f"Update indexes workflow submitted for document {document_id}, workflow ID: {workflow_result.id}")

    return workflow_result


# ========== Collection Tasks ==========

@current_app.task  # current_app：获取当前 Celery 应用实例（需提前初始化 Celery 应用，通常在项目中通过 Celery() 创建）。
def reconcile_indexes_task():
    """Periodic task to reconcile index specs with statuses"""
    try:
        logger.info("Starting index reconciliation")

        # Import here to avoid circular dependencies
        from aperag.tasks.reconciler import index_reconciler

        # Run reconciliation
        index_reconciler.reconcile_all()

        logger.info("Index reconciliation completed")

    except Exception as e:
        logger.error(f"Index reconciliation failed: {e}", exc_info=True)
        raise


@current_app.task
def reconcile_collection_summaries_task():
    """Periodic task to reconcile collection summary specs with statuses"""
    try:
        logger.info("Starting collection summary reconciliation")

        # Import here to avoid circular dependencies
        from aperag.tasks.reconciler import collection_summary_reconciler

        # Run reconciliation
        collection_summary_reconciler.reconcile_all()

        logger.info("Collection summary reconciliation completed")

    except Exception as e:
        logger.error(f"Collection summary reconciliation failed: {e}", exc_info=True)
        raise


@app.task(bind=True)
def collection_delete_task(self, collection_id: str) -> Any:
    """
    Delete collection task entry point

    Args:
        collection_id: Collection ID to delete
    """
    try:
        result = collection_task.delete_collection(collection_id)

        if not result.success:
            raise Exception(result.error)

        logger.info(f"Collection {collection_id} deleted successfully")
        return result.to_dict()

    except Exception as e:
        logger.error(f"Collection deletion failed for {collection_id}: {str(e)}")
        raise self.retry(
            exc=e,
            countdown=TaskConfig.RETRY_COUNTDOWN_COLLECTION,
            max_retries=TaskConfig.RETRY_MAX_RETRIES_COLLECTION,
        )


@app.task(bind=True)
def collection_init_task(self, collection_id: str, document_user_quota: int) -> Any:
    """
    Initialize collection task entry point

    Args:
        collection_id: Collection ID to initialize
        document_user_quota: User quota for documents
    """
    try:
        result = collection_task.initialize_collection(collection_id, document_user_quota)

        if not result.success:
            raise Exception(result.error)

        logger.info(f"Collection {collection_id} initialized successfully")
        return result.to_dict()

    except Exception as e:
        logger.error(f"Collection initialization failed for {collection_id}: {str(e)}")
        raise self.retry(
            exc=e,
            countdown=TaskConfig.RETRY_COUNTDOWN_COLLECTION,
            max_retries=TaskConfig.RETRY_MAX_RETRIES_COLLECTION,
        )


@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def collection_summary_task(self, summary_id: str, collection_id: str, target_version: int) -> Any:
    """
    Generate collection summary task entry point

    Args:
        summary_id: Summary ID to generate
        collection_id: Collection ID to generate summary for
    """
    try:
        from aperag.service.collection_summary_service import collection_summary_service

        collection_summary_service.generate_collection_summary_task(summary_id, collection_id, target_version)

        logger.info(f"Collection summary task completed for {collection_id}")
        return {"success": True, "collection_id": collection_id}

    except Exception as e:
        logger.error(f"Collection summary generation failed for {collection_id}: {str(e)}")

        # Mark as failed using callback if we've exhausted retries
        if self.request.retries >= self.max_retries:
            from aperag.tasks.reconciler import collection_summary_callbacks
            collection_summary_callbacks.on_summary_failed(collection_id, str(e))

        raise self.retry(
            exc=e,
            countdown=TaskConfig.RETRY_COUNTDOWN_COLLECTION,
            max_retries=TaskConfig.RETRY_MAX_RETRIES_COLLECTION,
        )


@current_app.task
def cleanup_expired_documents_task():
    """
    Celery task to clean up expired uploaded documents.
    This task should be scheduled to run periodically (e.g., every hour).
    """
    logger.info("Starting Celery task: cleanup_expired_documents")

    # Import here to avoid circular dependencies
    from aperag.tasks.reconciler import collection_gc_reconciler

    result = collection_gc_reconciler.reconcile_all()

    logger.info(f"Celery task completed with result: {result}")
    return result

# ========== Evaluation Tasks ==========

# By default, get_async_session() uses a global AsyncEngine object.
# Since we also use asyncio.run() to execute async functions, old connections
# in the AsyncEngine connection pool cannot work in the new event loop,
# which will raise an exception like "xxx attached to a different loop".
# Therefore, using a dedicated AsyncEngine to avoid issues from connection reuse.
@asynccontextmanager
async def _new_async_engine():
    from aperag.aperag_config import new_async_engine

    engine = new_async_engine()
    try:
        yield engine
    finally:
        await engine.dispose()


@current_app.task
def reconcile_evaluations_task():
    """Periodic task to reconcile evaluations."""
    try:
        async def execute():
            from aperag.service.evaluation_service import EvaluationExecutor

            async with _new_async_engine() as engine:
                executor = EvaluationExecutor(engine)
                await executor.schedule_evaluations()

        import asyncio
        asyncio.run(execute())

        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to reconcile evaluations: {e}", exc_info=True)
        raise


@app.task(bind=True)
def initialize_evaluation_task(self, evaluation_id: str) -> Any:
    """Task to initialize a specific evaluation."""
    try:
        async def execute():
            from aperag.service.evaluation_service import EvaluationExecutor

            async with _new_async_engine() as engine:
                executor = EvaluationExecutor(engine)
                await executor.initialize_evaluation(evaluation_id)

        import asyncio
        asyncio.run(execute())

        return {"success": True, "evaluation_id": evaluation_id}
    except Exception as e:
        logger.error(f"Failed to initialize evaluation {evaluation_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)


@app.task(bind=True)
def process_evaluation_batch_task(self, evaluation_id: str) -> Any:
    """Task to process a batch of items for an evaluation."""
    try:
        async def execute():
            from aperag.service.evaluation_service import EvaluationExecutor

            async with _new_async_engine() as engine:
                executor = EvaluationExecutor(engine)
                await executor.process_evaluation_batch(evaluation_id)

        import asyncio
        asyncio.run(execute())

        return {"success": True, "evaluation_id": evaluation_id}
    except Exception as e:
        logger.error(f"Failed to process batch for evaluation {evaluation_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)


@app.task(bind=True)
def process_evaluation_item_task(self, evaluation_id: str, item_id: str) -> Any:
    """Task to process a single evaluation item."""
    try:
        async def execute():
            from aperag.service.evaluation_service import EvaluationExecutor

            async with _new_async_engine() as engine:
                executor = EvaluationExecutor(engine)
                await executor.process_evaluation_item(evaluation_id, item_id)

        import asyncio
        asyncio.run(execute())

        return {"success": True, "item_id": item_id}
    except Exception as e:
        logger.error(f"Failed to process item {item_id}: {e}", exc_info=True)
        # You might want a different retry policy for item tasks
        raise self.retry(exc=e, countdown=60, max_retries=3)
