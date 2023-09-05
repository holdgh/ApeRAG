import datetime
import json
import logging
import os

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from config.celery import app
from kubechat.models import Document, DocumentStatus, Collection, CollectionStatus, CollectionSyncHistory
from kubechat.source.base import get_source
from kubechat.tasks.index import add_index_for_document, remove_index, update_index
from kubechat.utils.db import query_documents
from readers.readers import DEFAULT_FILE_READER_CLS

logger = logging.getLogger(__name__)


@app.task(bind=True)
def sync_documents(self, **kwargs):
    collection_id = kwargs["collection_id"]
    collection = Collection.objects.exclude(status=CollectionStatus.DELETED).get(
        id=int(collection_id)
    )
    source = get_source(json.loads(collection.config))
    if not source.sync_enabled():
        return -1
    sync_history = CollectionSyncHistory(
        user=collection.user,
        start_time=timezone.now(),
        collection=collection,
        execution_time=datetime.timedelta(seconds=0),
        total_documents_to_sync=0
    )
    logger.debug(f"sync_documents_cron_job() : sync collection{collection_id} start ")

    src_docs = {}
    source = get_source(json.loads(collection.config))
    for doc in source.scan_documents():
        if not os.path.splitext(doc.name)[1].lower() in DEFAULT_FILE_READER_CLS.keys():
            continue
        src_docs[doc.name] = doc

    dst_docs = {}
    for doc in query_documents(collection.user, collection_id):
        dst_docs[doc.name] = doc

    sync_history.total_documents = len(dst_docs)
    sync_history.save()
    # echo the id out of the task by self.update_state().
    self.update_state(state='SYNCHRONIZING', meta={'id': sync_history.id})
    logger.debug(f"sync_documents_cron_job() : sync collection{collection_id} start ")
    sync_history.update_execution_time()
    sync_history.save()

    for name, src_doc in src_docs.items():
        dst_doc = dst_docs.get(name, None)
        if dst_doc:
            metadata = json.loads(dst_doc.metadata)
            dst_modified_time = datetime.datetime.strptime(metadata["modified_time"], "%Y-%m-%dT%H:%M:%S")
            if src_doc.metadata["modified_time"] > dst_modified_time:  # modify
                sync_history.total_documents_to_sync = sync_history.total_documents_to_sync + 1
                sync_history.save()
                update_index.delay(dst_doc.id, sync_history.id)
        else:  # add
            sync_history.total_documents_to_sync = sync_history.total_documents_to_sync + 1
            doc = Document(
                user=collection.user,
                name=name,
                status=DocumentStatus.PENDING,
                size=src_doc.size,
                collection=collection,
                metadata=json.dumps(src_doc.metadata, cls=DjangoJSONEncoder),
            )
            doc.save()
            sync_history.save()
            add_index_for_document.delay(doc.id, sync_history.id)

    for name, dst_doc in dst_docs.items():  # delete
        if name not in src_docs.keys():
            sync_history.total_documents_to_sync = sync_history.total_documents_to_sync + 1
            sync_history.save()
            remove_index.delay(dst_doc.id, sync_history.id)
    sync_history.save()
    return sync_history.id
