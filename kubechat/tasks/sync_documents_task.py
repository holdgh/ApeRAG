import datetime
import json
import logging
import os
import time
from config.celery import app
from kubechat.models import Document, DocumentStatus, Collection, CollectionStatus, CollectionSyncHistory
from kubechat.tasks.index import add_index_for_document, remove_index, update_index
from kubechat.utils.db import query_collection, query_documents
from readers.Readers import DEFAULT_FILE_READER_CLS
from kubechat.source.base import Source, get_source
from django.utils import timezone

logger = logging.getLogger(__name__)


@app.task
def sync_documents(**kwargs):
    collection_id = kwargs["collection_id"]
    collection = Collection.objects.exclude(status=CollectionStatus.DELETED).get(
        id=int(collection_id)
    )
    collection_sync_history = CollectionSyncHistory(
        user=collection.user,
        start_time=timezone.now(),
        collection=collection,
        execution_time=datetime.timedelta(seconds=0),
        total_documents_to_sync=0
    )
    logger.debug(f"sync_documents_cron_job() : sync collection{collection_id} start ")
    source = get_source(collection, json.loads(collection.config))
    documents_in_remote = {}
    documents_in_db = {}

    for document in source.scan_documents():
        documents_in_remote[document.name] = document
    for document in Document.objects.exclude(status=DocumentStatus.DELETED).filter(
            user=collection.user, collection_id=collection_id
    ):
        documents_in_db[document.name] = document

    collection_sync_history.total_documents = len(documents_in_db)
    collection_sync_history.update_execution_time()
    collection_sync_history.save()
    collection_sync_history_id = collection_sync_history.id

    for name_remote, document_remote in documents_in_remote.items():
        if name_remote in documents_in_db.keys():
            document_db = documents_in_db[name_remote]
            if document_remote.metadata > document_db.metadata:  # modify
                collection_sync_history.total_documents_to_sync = collection_sync_history.total_documents_to_sync + 1
                collection_sync_history.save()
                update_index.delay(document_db.id, collection_sync_history_id)
        else:  # add
            collection_sync_history.total_documents_to_sync = collection_sync_history.total_documents_to_sync + 1
            document_remote.save()
            collection_sync_history.save()
            add_index_for_document.delay(document_remote.id, collection_sync_history_id)

    for name_db, document_db in documents_in_db.items():  # delete
        if name_db not in documents_in_remote.keys():
            collection_sync_history.total_documents_to_sync = collection_sync_history.total_documents_to_sync + 1
            collection_sync_history.save()
            remove_index.delay(document_db.id, collection_sync_history_id)
    collection_sync_history.save()
    return collection_sync_history.id
