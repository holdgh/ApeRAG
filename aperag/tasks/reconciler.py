# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import List, Optional

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from aperag.aperag_config import get_sync_session
from aperag.db.models import (
    Collection,
    CollectionStatus,
    CollectionSummary,
    CollectionSummaryStatus,
    Document,
    DocumentIndex,
    DocumentIndexStatus,
    DocumentIndexType,
    DocumentStatus,
)
from aperag.schema.utils import parseCollectionConfig
from aperag.tasks.scheduler import TaskScheduler, create_task_scheduler
from aperag.utils.constant import IndexAction
from aperag.utils.utils import utc_now

logger = logging.getLogger(__name__)


class DocumentIndexReconciler:  # 文档索引协调器
    """Reconciler for document indexes using single status model"""

    def __init__(self, task_scheduler: Optional[TaskScheduler] = None, scheduler_type: str = "celery"):
        self.task_scheduler = task_scheduler or create_task_scheduler(scheduler_type)  # 默认采用CeleryTaskScheduler实例

    def reconcile_all(self):
        """
        Main reconciliation loop - scan indexes and reconcile differences
        Groups operations by document and index type for atomic processing
        """
        # Get all indexes that need reconciliation
        """
        因为 get_sync_session() 是生成器（yield 返回值），生成器需要通过迭代（for 循环）获取值。
        这里的循环只会执行一次（生成器只产生一个会话对象），本质是借助迭代触发生成器的上下文管理逻辑（确保会话正确释放）。
        
        # 等效逻辑（更易理解）
        with get_sync_session() as session:
            operations = self._get_indexes_needing_reconciliation(session)

        """
        for session in get_sync_session():  # 获取数据库连接池中的连接【会话】
            # 形如：{"文档1_id": {IndexAction.CREATE: [], IndexAction.UPDATE: [], IndexAction.DELETE: []}, "文档2_id": {IndexAction.CREATE: [], IndexAction.UPDATE: [], IndexAction.DELETE: []}, ...}
            operations = self._get_indexes_needing_reconciliation(session)  # 从数据库获取需要处理的索引操作

        logger.info(f"Found {len(operations)} documents need to be reconciled")

        # Process each document with its own transaction
        successful_docs = 0
        failed_docs = 0
        for document_id, doc_operations in operations.items():  # 逐个文档处理索引任务
            try:
                self._reconcile_single_document(document_id, doc_operations)
                successful_docs += 1
            except Exception as e:
                failed_docs += 1
                logger.error(f"Failed to reconcile document {document_id}: {e}", exc_info=True)
                # Continue processing other documents - don't let one failure stop everything

        logger.info(f"Reconciliation completed: {successful_docs} successful, {failed_docs} failed")

    def _get_indexes_needing_reconciliation(self, session: Session) -> List[DocumentIndex]:  # 从数据库查询待处理的索引操作【创建、更新、删除】
        """
        Get all indexes that need reconciliation without modifying their state.
        State modifications will happen in individual document transactions.
        """
        from collections import defaultdict

        operations = defaultdict(lambda: {IndexAction.CREATE: [], IndexAction.UPDATE: [], IndexAction.DELETE: []})  # 初始索引操作任务集合，三类操作：创建、更新、删除
        # 下述定义了索引任务的创建、更新、删除的查询条件表达式【这些任务的创建由外部触发，python后端仅作相应版本号及状态的更新，实际的操作由celery服务处理】
        conditions = {
            IndexAction.CREATE: and_(
                DocumentIndex.status == DocumentIndexStatus.PENDING,
                DocumentIndex.observed_version < DocumentIndex.version,  # 已处理过的版本号小于更新后的版本号【表示存在未处理的索引任务】【确保 “存在未处理的新版本”】
                DocumentIndex.version == 1,  # 版本号初始为1，标识首次创建索引
            ),
            IndexAction.UPDATE: and_(
                DocumentIndex.status == DocumentIndexStatus.PENDING,
                DocumentIndex.observed_version < DocumentIndex.version,  # 已处理过的版本号小于更新后的版本号【表示存在未处理的索引任务】【确保 “存在未处理的新版本”】
                DocumentIndex.version > 1,  # 版本号大于1，标识更新索引操作
            ),
            IndexAction.DELETE: and_(
                DocumentIndex.status == DocumentIndexStatus.DELETING,  # 删除条件：索引任务状态为DELETING
            ),
        }  # 三类待处理索引操作的条件表达式定义

        for action, condition in conditions.items():
            stmt = select(DocumentIndex).where(condition)
            result = session.execute(stmt)  # 利用数据库连接会话执行查询待处理索引数据
            indexes = result.scalars().all()
            for index in indexes:
                operations[index.document_id][action].append(index)
        # 形如：{"文档1_id": {IndexAction.CREATE: [], IndexAction.UPDATE: [], IndexAction.DELETE: []}, "文档2_id": {IndexAction.CREATE: [], IndexAction.UPDATE: [], IndexAction.DELETE: []}, ...}
        return operations  # 字典类型，三类待处理的索引数据集合

    def _reconcile_single_document(self, document_id: str, operations: dict):  # 处理单个文档的索引任务
        """
        Reconcile operations for a single document within its own transaction
        """
        for session in get_sync_session():
            # Collect indexes for this document that need claiming
            indexes_to_claim = []

            for action, doc_indexes in operations.items():
                for doc_index in doc_indexes:  # 逐个收集索引任务的处理参数【索引任务id、索引类型【向量、全文、图、视觉、摘要】、索引操作【增删改】】
                    indexes_to_claim.append((doc_index.id, doc_index.index_type, action))

            # -- 更新当前文档的索引任务状态，返回更新成功的索引任务信息
            # Atomically claim the indexes for this document
            claimed_indexes = self._claim_document_indexes(session, document_id, indexes_to_claim)

            if claimed_indexes:
                # Schedule tasks for successfully claimed indexes
                # -- 对于任务状态更新成功的索引任务，进行处理
                self._reconcile_document_operations(document_id, claimed_indexes)
                session.commit()
            else:
                # Some indexes couldn't be claimed (likely already being processed), skip this document
                logger.debug(f"Skipping document {document_id} - indexes already being processed")

    def _claim_document_indexes(self, session: Session, document_id: str, indexes_to_claim: List[tuple]) -> List[dict]:  # 更新索引任务的状态标识【由pending更新为creating、由deleting更新为deletion in progress】
        """
        Atomically claim indexes for a document by updating their state.
        Returns list of successfully claimed indexes with their details.
        """
        claimed_indexes = []

        try:
            for index_id, index_type, action in indexes_to_claim:  # 逐条索引任务状态更新处理
                # -- 设置不同索引任务的状态更新目标
                if action in [IndexAction.CREATE, IndexAction.UPDATE]:  # 对应索引任务状态为pending
                    target_state = DocumentIndexStatus.CREATING
                elif action == IndexAction.DELETE:  # 对应索引任务状态为deleting
                    target_state = DocumentIndexStatus.DELETION_IN_PROGRESS
                else:
                    continue
                # -- 依据索引任务id查询索引任务记录
                # Get the current index record to extract version info
                stmt = select(DocumentIndex).where(DocumentIndex.id == index_id)
                result = session.execute(stmt)
                current_index = result.scalar_one_or_none()

                if not current_index:
                    continue
                # -- 设置不同索引操作的更新条件【在前期查询待处理任务条件基础上，加了索引任务id的过滤】
                # 此处的更新条件，之前的状态条件不可缺失，否则可能引发数据安全。比如在当前更新之前，其他线程已更新了状态信息，若此处不对状态信息进行校验，则会导致状态信息的更新不符合业务逻辑
                # Build appropriate claiming conditions based on operation type
                if action == IndexAction.CREATE:
                    claiming_conditions = [
                        DocumentIndex.id == index_id,
                        DocumentIndex.status == DocumentIndexStatus.PENDING,
                        DocumentIndex.observed_version < DocumentIndex.version,
                        DocumentIndex.version == 1,
                    ]
                elif action == IndexAction.UPDATE:
                    claiming_conditions = [
                        DocumentIndex.id == index_id,
                        DocumentIndex.status == DocumentIndexStatus.PENDING,
                        DocumentIndex.observed_version < DocumentIndex.version,
                        DocumentIndex.version > 1,
                    ]
                elif action == IndexAction.DELETE:
                    claiming_conditions = [
                        DocumentIndex.id == index_id,
                        DocumentIndex.status == DocumentIndexStatus.DELETING,
                    ]
                # -- 执行更新索引任务状态
                # Try to claim this specific index
                update_stmt = (
                    update(DocumentIndex)
                    .where(and_(*claiming_conditions))  # 更新条件
                    .values(status=target_state, gmt_updated=utc_now(), gmt_last_reconciled=utc_now())  # 要更新的值
                )

                result = session.execute(update_stmt)
                # -- 根据更新操作返回值【更新成功的行数】判断更新是否成功【若更新成功，则将索引信息收集到claimed_indexes】
                if result.rowcount > 0:
                    # Successfully claimed this index
                    claimed_indexes.append(
                        {
                            "index_id": index_id,
                            "document_id": document_id,
                            "index_type": index_type,
                            "action": action,
                            "target_version": current_index.version
                            if action in [IndexAction.CREATE, IndexAction.UPDATE]
                            else None,  # 目标版本号，当且仅当索引任务为新增或修改时才为索引记录的最新版本号，否则为None
                        }
                    )
                    logger.debug(f"Claimed index {index_id} for document {document_id} ({action})")
                else:
                    logger.debug(f"Could not claim index {index_id} for document {document_id}")

            session.flush()  # Ensure changes are visible【执行sql和commit之间的中间状态，提交sql到数据库中执行，但是执行的数据仅在当前会话中可见，除非设置数据库隔离级别为 READ UNCOMMITTED】
            # 返回更新索引任务状态成功的索引信息
            return claimed_indexes
        except Exception as e:
            logger.error(f"Failed to claim indexes for document {document_id}: {e}")
            return []

    def _reconcile_document_operations(self, document_id: str, claimed_indexes: List[dict]):  # 处理单个文档的索引任务【每种索引任务仅对应一条索引记录】
        """
        Reconcile operations for a single document, batching same operation types together
        """
        from collections import defaultdict
        # -- 将索引任务按照操作类型【增删改】分类收集
        # Group by operation type to batch operations
        operations_by_type = defaultdict(list)
        for claimed_index in claimed_indexes:
            action = claimed_index["action"]
            operations_by_type[action].append(claimed_index)
        # -- 处理创建类索引任务
        # Process create operations as a batch
        if IndexAction.CREATE in operations_by_type:
            create_indexes = operations_by_type[IndexAction.CREATE]
            create_types = [claimed_index["index_type"] for claimed_index in create_indexes]  # 获取索引类型
            context = {}
            # -- 按照索引类型收集相应的索引任务版本号
            for claimed_index in create_indexes:
                index_type = claimed_index["index_type"]
                target_version = claimed_index.get("target_version")

                # Store version info in context
                if target_version is not None:
                    context[f"{index_type}_version"] = target_version  # 对于一个文档，由于一种索引仅对应一条索引记录，则此处按照索引类型收集版本号信息是可行的【不会出现一种索引对应两个及以上的版本号】
            # -- 批量处理当前文档的创建类索引任务
            self.task_scheduler.schedule_create_index(
                document_id=document_id, index_types=create_types, context=context
            )
            logger.info(f"Scheduled create task for document {document_id}, types: {create_types}")
        # -- 处理更新类索引任务
        # Process update operations as a batch
        if IndexAction.UPDATE in operations_by_type:
            update_indexes = operations_by_type[IndexAction.UPDATE]
            update_types = [claimed_index["index_type"] for claimed_index in update_indexes]
            context = {}

            for claimed_index in update_indexes:
                index_type = claimed_index["index_type"]
                target_version = claimed_index.get("target_version")

                # Store version info in context
                if target_version is not None:
                    context[f"{index_type}_version"] = target_version

            self.task_scheduler.schedule_update_index(
                document_id=document_id, index_types=update_types, context=context
            )
            logger.info(f"Scheduled update task for document {document_id}, types: {update_types}")
        # -- 处理删除类索引任务
        # Process delete operations as a batch
        if IndexAction.DELETE in operations_by_type:
            delete_indexes = operations_by_type[IndexAction.DELETE]
            delete_types = [claimed_index["index_type"] for claimed_index in delete_indexes]

            self.task_scheduler.schedule_delete_index(document_id=document_id, index_types=delete_types)
            logger.info(f"Scheduled delete task for document {document_id}, types: {delete_types}")


# Index task completion callbacks
class IndexTaskCallbacks:  # 索引任务完成时的回调操作
    """Callbacks for index task completion"""

    @staticmethod
    def _update_document_status(document_id: str, session: Session):  # 更新文档记录
        stmt = select(Document).where(
            Document.id == document_id,
            Document.status.not_in([DocumentStatus.DELETED, DocumentStatus.UPLOADED, DocumentStatus.EXPIRED]),
        )
        result = session.execute(stmt)
        document = result.scalar_one_or_none()
        if not document:
            return
        document.status = document.get_overall_index_status(session)  # 根据索引任务的状态获取相应文档接下来要更新的目标状态
        """
        在 SQLAlchemy 中，`session.add(document)` 的核心作用是**将修改后的状态的 `document` 对象添加到当前数据库会话（Session）的“待处理队列”中**，但它**并不直接执行数据库的更新操作**。具体含义和作用如下：
        
        
        ### 1. `session.add(document)` 的本质：“标记待更新”
        在 SQLAlchemy 的 ORM 机制中，`session`（数据库会话）扮演着“中间协调者”的角色：
        - 当你通过 `document.status = ...` 修改了对象的属性（如文档状态），这只是在**内存中修改了 Python 对象**，并未同步到数据库；
        - 调用 `session.add(document)` 是告诉会话：“这个 `document` 对象的状态已经被修改，请在合适的时机将这些修改同步到数据库”。
        
        简单说，这一步是**“登记修改”**，而非“执行更新”——修改暂时存放在会话的内存缓存中，等待后续的 `session.commit()` 触发真正的数据库操作。
        
        
        ### 2. 为什么需要 `session.add(document)`？
        在你的代码中，`document` 是通过 `session.execute(stmt)` 从数据库查询得到的对象（属于“会话托管对象”），理论上修改其属性后，SQLAlchemy 会自动跟踪到变化，无需手动 `add`。但这里显式调用 `session.add(document)` 通常有两个原因：
        
        - **兼容性保障**：  
          若 `document` 对象因某些原因脱离了会话的跟踪（如跨会话传递对象、会话配置特殊），`session.add()` 可强制将其重新纳入会话管理，确保修改被正确跟踪。
        
        - **代码可读性**：  
          显式调用 `add()` 是一种“自文档化”的做法，明确告诉阅读者：“这个对象的修改需要被持久化到数据库”，避免因隐性逻辑（自动跟踪）导致误解。
        
        
        ### 3. 真正执行数据库更新的操作：`session.commit()`
        `session.add(document)` 只是“标记修改”，而**数据库的实际更新（`UPDATE` 语句）要等到 `session.commit()` 被调用时才会执行**。流程如下：
        1. `document.status = ...` → 内存中修改对象属性；
        2. `session.add(document)` → 会话登记该对象的修改；
        3. `session.commit()` → 会话将所有登记的修改（包括 `document` 的状态更新）生成 `UPDATE` 语句，发送到数据库执行，并提交事务。
        
        若没有 `session.commit()`，即使调用了 `session.add()`，修改也只会停留在内存中，不会同步到数据库表中。
        
        
        ### 总结
        - `session.add(document)` 的作用是**将修改后的文档对象纳入会话的更新跟踪队列**，为后续的数据库同步做准备；
        - 它**不是直接执行更新**，真正的数据库更新由 `session.commit()` 触发；
        - 这段代码中，`session.add()` 更多是出于“兼容性”和“可读性”的考虑，确保文档状态的修改能被会话正确捕获并最终同步到数据库。
        """
        session.add(document)  # 文档要更新的状态登记到当前session中，待后续session.commit()时真正执行更新

    @staticmethod
    def on_index_created(document_id: str, index_type: str, target_version: int, index_data: str = None):  # 处理新增/修改索引任务成功时的回调操作
        """Called when index creation/update succeeds"""
        for session in get_sync_session():
            # -- 设置更新索引任务的条件及更新字段
            # Use atomic update with version validation
            update_stmt = (
                update(DocumentIndex)
                .where(
                    and_(
                        DocumentIndex.document_id == document_id,
                        DocumentIndex.index_type == DocumentIndexType(index_type),
                        DocumentIndex.status == DocumentIndexStatus.CREATING,  # 验证状态，乐观锁机制
                        DocumentIndex.version == target_version,  # Critical: validate version  验证版本号，乐观锁机制
                    )
                )
                .values(
                    status=DocumentIndexStatus.ACTIVE,  # 索引任务状态 ACTIVE 表示索引数据处理完成，目前可用
                    observed_version=target_version,  # Mark this version as processed  将最新处理版本号更新为version，表示当前索引任务已处理
                    index_data=index_data,  # 索引任务的处理结果【json格式，表示当前索引任务的处理结果说明】
                    error_message=None,
                    gmt_updated=utc_now(),
                    gmt_last_reconciled=utc_now(),
                )  # 要更新的值
            )
            # -- 执行更新操作
            result = session.execute(update_stmt)
            # -- 验证更新是否成功【若成功，则更新文档状态；否则回滚】
            if result.rowcount > 0:
                IndexTaskCallbacks._update_document_status(document_id, session)  # 注意这里仅是向session登记了文档要更新的状态
                logger.info(f"{index_type} index creation completed for document {document_id} (v{target_version})")
                session.commit()  # 在这里真正更新文档状态
            else:
                logger.warning(
                    f"Index creation callback ignored for document {document_id} type {index_type} v{target_version} - not in expected state"
                )
                session.rollback()

    @staticmethod
    def on_index_failed(document_id: str, index_type: str, error_message: str):  # 索引任务处理失败的回调操作
        """Called when index operation fails"""
        for session in get_sync_session():
            # Use atomic update with state validation
            update_stmt = (
                update(DocumentIndex)
                .where(
                    and_(
                        DocumentIndex.document_id == document_id,
                        DocumentIndex.index_type == DocumentIndexType(index_type),
                        # Allow transition from any in-progress state
                        DocumentIndex.status.in_(
                            [DocumentIndexStatus.CREATING, DocumentIndexStatus.DELETION_IN_PROGRESS]
                        ),
                    )
                )
                .values(
                    status=DocumentIndexStatus.FAILED,
                    error_message=error_message,
                    gmt_updated=utc_now(),
                    gmt_last_reconciled=utc_now(),
                )
            )

            result = session.execute(update_stmt)
            if result.rowcount > 0:
                IndexTaskCallbacks._update_document_status(document_id, session)
                logger.error(f"{index_type} index operation failed for document {document_id}: {error_message}")
                session.commit()
            else:
                logger.warning(
                    f"Index failure callback ignored for document {document_id} type {index_type} - not in expected state"
                )
                session.rollback()

    @staticmethod
    def on_index_deleted(document_id: str, index_type: str):  # 处理删除索引任务成功时的回调操作
        """Called when index deletion succeeds - hard delete the record"""
        for session in get_sync_session():
            # Delete the record entirely
            from sqlalchemy import delete

            delete_stmt = delete(DocumentIndex).where(
                and_(
                    DocumentIndex.document_id == document_id,
                    DocumentIndex.index_type == DocumentIndexType(index_type),
                    DocumentIndex.status == DocumentIndexStatus.DELETION_IN_PROGRESS,
                )
            )

            result = session.execute(delete_stmt)
            if result.rowcount > 0:
                IndexTaskCallbacks._update_document_status(document_id, session)
                logger.info(f"{index_type} index deleted for document {document_id}")
                session.commit()
            else:
                logger.warning(
                    f"Index deletion callback ignored for document {document_id} type {index_type} - not in expected state"
                )
                session.rollback()


class CollectionSummaryReconciler:
    """Reconciler for collection summaries using reconcile pattern"""

    def __init__(self, scheduler_type: str = "celery"):
        self.scheduler_type = scheduler_type

    def reconcile_all(self):
        """
        Main reconciliation loop - scan collections and reconcile summary differences
        """
        for session in get_sync_session():
            summaries_to_reconcile = self._get_summaries_needing_reconciliation(session)
            logger.info(f"Found {len(summaries_to_reconcile)} collection summaries need reconciliation")

            successful_reconciliations = 0
            failed_reconciliations = 0
            for summary in summaries_to_reconcile:
                try:
                    self._reconcile_single_summary(session, summary)
                    successful_reconciliations += 1
                except Exception as e:
                    failed_reconciliations += 1
                    logger.error(f"Failed to reconcile collection summary {summary.id}: {e}", exc_info=True)

            if successful_reconciliations > 0 or failed_reconciliations > 0:
                logger.info(
                    f"Summary reconciliation completed: {successful_reconciliations} successful, {failed_reconciliations} failed"
                )

    def _get_summaries_needing_reconciliation(self, session: Session) -> List[CollectionSummary]:
        """
        Get all collection summaries that need reconciliation
        """
        stmt = select(CollectionSummary).where(
            or_(
                CollectionSummary.version != CollectionSummary.observed_version,
                CollectionSummary.status != CollectionSummaryStatus.GENERATING,
            )
        )
        result = session.execute(stmt)
        return result.scalars().all()

    def _reconcile_single_summary(self, session: Session, summary: CollectionSummary):
        """
        Reconcile summary generation for a single collection summary
        """
        claimed = self._claim_summary_for_processing(session, summary.id, summary.version)

        if claimed:
            self._schedule_summary_generation(summary.id, summary.collection_id, summary.version)
            session.commit()
        else:
            logger.debug(
                f"Skipping summary {summary.id} - could not be claimed (likely already processing or version mismatch)"
            )

    def _claim_summary_for_processing(self, session: Session, summary_id: str, version: int) -> bool:
        """Atomically claim a summary for processing by updating its state and observed_version"""
        try:
            update_stmt = (
                update(CollectionSummary)
                .where(
                    and_(
                        CollectionSummary.id == summary_id,
                        CollectionSummary.status != CollectionSummaryStatus.GENERATING,
                        CollectionSummary.version == version,
                    )
                )
                .values(
                    status=CollectionSummaryStatus.GENERATING,
                    gmt_last_reconciled=utc_now(),
                    gmt_updated=utc_now(),
                )
            )
            result = session.execute(update_stmt)
            if result.rowcount > 0:
                logger.debug(f"Claimed summary {summary_id} (v{version}) for processing")
                session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to claim summary {summary_id}: {e}")
            session.rollback()
            return False

    def _schedule_summary_generation(self, summary_id: str, collection_id: str, target_version: int):
        """
        Schedule summary generation task
        """
        try:
            from config.celery_tasks import collection_summary_task

            task_result = collection_summary_task.delay(summary_id, collection_id, target_version)
            logger.info(
                f"Collection summary generation task scheduled for summary {summary_id} "
                f"(collection: {collection_id}, version: {target_version}), task ID: {task_result.id}"
            )
        except Exception as e:
            logger.error(f"Failed to schedule summary generation for {summary_id}: {e}")
            raise


class CollectionSummaryCallbacks:
    """Callbacks for collection summary task completion"""

    @staticmethod
    def on_summary_generated(summary_id: str, summary_content: str, target_version: int):
        """Called when summary generation succeeds"""
        try:
            for session in get_sync_session():
                # First, get the collection summary record to get collection_id
                summary_query = select(CollectionSummary).where(
                    and_(
                        CollectionSummary.id == summary_id,
                        CollectionSummary.status == CollectionSummaryStatus.GENERATING,
                        CollectionSummary.version == target_version,
                    )
                )
                summary_result = session.execute(summary_query)
                summary_record = summary_result.scalar_one_or_none()

                if not summary_record:
                    logger.warning(
                        f"Summary completion callback ignored for {summary_id} (v{target_version}) - not in expected state"
                    )
                    return

                collection_id = summary_record.collection_id

                # Get collection info to check if summary is enabled and get current gmt_updated
                collection_query = select(Collection).where(
                    and_(Collection.id == collection_id, Collection.gmt_deleted.is_(None))
                )
                collection_result = session.execute(collection_query)
                collection_record = collection_result.scalar_one_or_none()

                if not collection_record:
                    logger.error(f"Collection {collection_id} not found during summary completion")
                    return

                # Check if summary is enabled in collection config
                try:
                    config = parseCollectionConfig(collection_record.config)
                    is_summary_enabled = config.enable_summary
                except Exception as e:
                    logger.error(f"Failed to parse collection config for {collection_id}: {e}")
                    is_summary_enabled = False

                current_time = utc_now()
                collection_updated_time = collection_record.gmt_updated

                # Update collection_summary table
                summary_update_stmt = (
                    update(CollectionSummary)
                    .where(
                        and_(
                            CollectionSummary.id == summary_id,
                            CollectionSummary.status == CollectionSummaryStatus.GENERATING,
                            CollectionSummary.version == target_version,
                        )
                    )
                    .values(
                        status=CollectionSummaryStatus.COMPLETE,
                        summary=summary_content,
                        error_message=None,
                        observed_version=target_version,
                        gmt_updated=current_time,
                    )
                )
                summary_update_result = session.execute(summary_update_stmt)

                if summary_update_result.rowcount == 0:
                    session.rollback()
                    logger.warning(
                        f"Summary completion callback ignored for {summary_id} (v{target_version}) - summary not in expected state"
                    )
                    return

                # Update collection table if summary is enabled and collection hasn't been updated since we read it
                if is_summary_enabled and summary_content:
                    collection_update_stmt = (
                        update(Collection)
                        .where(
                            and_(
                                Collection.id == collection_id,
                                Collection.gmt_updated == collection_updated_time,  # Race condition prevention
                                Collection.gmt_deleted.is_(None),
                            )
                        )
                        .values(
                            description=summary_content,
                            gmt_updated=current_time,
                        )
                    )
                    collection_update_result = session.execute(collection_update_stmt)

                    if collection_update_result.rowcount > 0:
                        logger.info(f"Updated collection {collection_id} description with generated summary")
                    else:
                        logger.warning(
                            f"Failed to update collection {collection_id} description - collection may have been modified concurrently"
                        )

                session.commit()
                logger.info(f"Collection summary generation completed for {summary_id} (v{target_version})")

        except Exception as e:
            logger.error(f"Failed to update collection summary completion for {summary_id}: {e}")
            try:
                session.rollback()
            except Exception:
                pass

    @staticmethod
    def on_summary_failed(summary_id: str, error_message: str, target_version: int):
        """Called when summary generation fails"""
        try:
            for session in get_sync_session():
                update_stmt = (
                    update(CollectionSummary)
                    .where(
                        and_(
                            CollectionSummary.id == summary_id,
                            CollectionSummary.status == CollectionSummaryStatus.GENERATING,
                            CollectionSummary.version == target_version,
                        )
                    )
                    .values(
                        status=CollectionSummaryStatus.FAILED,
                        error_message=error_message,
                        gmt_updated=utc_now(),
                    )
                )
                result = session.execute(update_stmt)
                if result.rowcount > 0:
                    session.commit()
                    logger.error(
                        f"Collection summary generation failed for {summary_id} (v{target_version}): {error_message}"
                    )
                else:
                    session.rollback()
                    logger.warning(
                        f"Summary failure callback ignored for {summary_id} (v{target_version}) - not in expected state"
                    )
        except Exception as e:
            logger.error(f"Failed to update collection summary failure for {summary_id}: {e}")


class CollectionGCReconciler:
    def __init__(self, scheduler_type: str = "celery"):
        self.scheduler_type = scheduler_type

    def reconcile_all(self):
        collections = None
        for session in get_sync_session():
            stmt = select(Collection).where(
                or_(
                    Collection.status == CollectionStatus.ACTIVE,
                )
            )
            result = session.execute(stmt)
            collections = result.scalars().all()

        if not collections:
            return

        from aperag.tasks.collection import collection_task

        for collection in collections:
            collection_task.cleanup_expired_documents(collection.id)


# Global instances
index_reconciler = DocumentIndexReconciler()  # 文档索引协调器全局实例
index_task_callbacks = IndexTaskCallbacks()
collection_summary_reconciler = CollectionSummaryReconciler()
collection_summary_callbacks = CollectionSummaryCallbacks()
collection_gc_reconciler = CollectionGCReconciler()
