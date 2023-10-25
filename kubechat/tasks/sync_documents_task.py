import datetime
import json
import logging
import os
import sys
import traceback

from asgiref.sync import async_to_sync
from celery import group
from celery.result import GroupResult

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from pydantic import BaseModel

from config.celery import app
from kubechat.models import Document, DocumentStatus, Collection, CollectionStatus, CollectionSyncHistory, \
    CollectionSyncStatus
from kubechat.source.base import get_source
from kubechat.tasks.index import add_index_for_document, remove_index, update_index
from kubechat.utils.db import query_documents
from readers.readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


@app.task(bind=True)
def sync_documents(self, **kwargs):
    collection_id = kwargs["collection_id"]
    collection = Collection.objects.exclude(status=CollectionStatus.DELETED).get(id=collection_id)
    source = get_source(json.loads(collection.config))
    if not source.sync_enabled():
        return -1

    sync_history_id = kwargs.get("sync_history_id", None)
    if sync_history_id:
        collection_sync_history = CollectionSyncHistory.objects.get(id=sync_history_id)
    else:
        collection_sync_history = CollectionSyncHistory(
            user=collection.user,
            start_time=timezone.now(),
            collection=collection,
            execution_time=datetime.timedelta(seconds=0),
            total_documents_to_sync=0,
            status=CollectionSyncStatus.RUNNING,
        )
    logger.debug(f"sync_documents_cron_job() : sync collection{collection_id} start ")

    dst_docs = {}
    pr = async_to_sync(query_documents)(user=collection.user, collection_id=collection_id, pq=None)
    for doc in pr.data:
        dst_docs[doc.name] = doc

    task_context = {
        "scan_task_id": self.request.id,
    }
    collection_sync_history.task_context = task_context
    collection_sync_history.save()
    # echo the id out of the task by self.update_state().
    self.update_state(state='SYNCHRONIZING', meta={'id': collection_sync_history.id})
    logger.debug(f"sync_documents_cron_job() : sync collection{collection_id} start ")
    collection_sync_history.update_execution_time()
    collection_sync_history.save()

    src_docs = {}
    tasks = []
    source = get_source(json.loads(collection.config))
    for src_doc in source.scan_documents():
        if not os.path.splitext(src_doc.name)[1].lower() in DEFAULT_FILE_READER_CLS.keys():
            continue
        if src_doc.name in src_docs:
            logger.warning(f"Duplicate document {src_doc.name}")
            continue

        src_docs[src_doc.name] = src_doc
        collection_sync_history.total_documents += 1
        collection_sync_history.pending_documents += 1
        dst_doc = dst_docs.get(src_doc.name, None)
        if dst_doc:
            # modify
            metadata = json.loads(dst_doc.metadata)
            dst_modified_time = datetime.datetime.strptime(metadata["modified_time"], "%Y-%m-%dT%H:%M:%S")
            if src_doc.metadata["modified_time"] > dst_modified_time or dst_doc.status == DocumentStatus.PENDING:
                collection_sync_history.total_documents_to_sync += 1
                collection_sync_history.modified_documents += 1
                collection_sync_history.save()
                tasks.append(update_index.s(dst_doc.id))

        else:  # add
            collection_sync_history.total_documents_to_sync += 1
            collection_sync_history.new_documents += 1
            doc = Document(
                user=collection.user,
                name=src_doc.name,
                status=DocumentStatus.PENDING,
                size=src_doc.size,
                collection=collection,
                metadata=json.dumps(src_doc.metadata, cls=DjangoJSONEncoder),
            )
            doc.save()
            collection_sync_history.save()
            tasks.append(add_index_for_document.s(doc.id))

    for name, dst_doc in dst_docs.items():  # delete
        if name not in src_docs.keys():
            collection_sync_history.total_documents_to_sync = collection_sync_history.total_documents_to_sync + 1
            collection_sync_history.deleted_documents += 1
            collection_sync_history.pending_documents += 1
            collection_sync_history.save()
            tasks.append(remove_index.s(dst_doc.id))
    index_result = group(tasks).apply_async()
    index_result.save()
    monitor_result = monitor_sync_tasks.apply_async(args=[collection_sync_history.id])
    task_context["index_task_group_id"] = index_result.id
    task_context["monitor_task_id"] = monitor_result.id
    collection_sync_history.task_context = task_context
    collection_sync_history.save()


class SyncProgress(BaseModel):
    successful_documents: int = 0
    failed_documents: int = 0
    processing_documents: int = 0
    pending_documents: int = 0


def get_sync_progress(collection_sync_history):
    task_context = collection_sync_history.task_context
    progress = SyncProgress()
    if not task_context:
        return progress
    group_id = task_context.get("index_task_group_id", None)
    if not group_id:
        return progress
    group_result = GroupResult.restore(group_id, app=app)
    for task in group_result.results:
        status = task.status
        match status:
            case "STARTED" | "RETRY":
                progress.processing_documents += 1
            case "SUCCESS":
                progress.successful_documents += 1
            case "FAILURE":
                progress.failed_documents += 1
            case "PENDING":
                progress.pending_documents += 1
            case "REVOKED":
                pass
            case _:
                sys.exit(f"Unknown task status {status}")
    return progress


@app.task(bind=True)
def monitor_sync_tasks(self, collection_sync_history_id):
    collection_sync_history = CollectionSyncHistory.objects.get(id=collection_sync_history_id)
    if collection_sync_history.status == CollectionSyncStatus.COMPLETED:
        return

    progress = get_sync_progress(collection_sync_history)

    if progress.processing_documents == 0 and progress.pending_documents == 0:
        CollectionSyncHistory.objects.filter(id=collection_sync_history_id, status=CollectionSyncStatus.RUNNING).update(
            status=CollectionSyncStatus.COMPLETED,
            pending_documents=progress.pending_documents,
            processing_documents=progress.processing_documents,
            successful_documents=progress.successful_documents,
            failed_documents=progress.failed_documents,
        )
    elif collection_sync_history.status == CollectionSyncStatus.CANCELED:
        CollectionSyncHistory.objects.filter(id=collection_sync_history_id, status=CollectionSyncStatus.CANCELED).update(
            pending_documents=progress.pending_documents,
            processing_documents=progress.processing_documents,
            successful_documents=progress.successful_documents,
            failed_documents=progress.failed_documents,
        )
    else:
        # Maximum number of retries before giving up.
        # A value of None means task will retry forever. By default, this option is set to 3.
        raise self.retry(countdown=5, max_retries=None)
