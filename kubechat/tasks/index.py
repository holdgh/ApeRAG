import json
import logging
from datetime import datetime

from django.db.models import F
from django.utils import timezone

import time
from celery import Task
from config.celery import app

from config.vector_db import get_vector_db_connector
from readers.local_path_embedding import LocalPathEmbedding
from kubechat.source.base import get_source
from kubechat.utils.utils import generate_vector_db_collection_id
from kubechat.models import Document, DocumentStatus, CollectionStatus
from kubechat.models import Document, DocumentStatus, CollectionStatus, CollectionSyncHistory

logger = logging.getLogger(__name__)


def generate_qdrant_collection_id(user, collection) -> str:
    return str(user).replace('|', '-') + "-" + str(collection)


class CustomLoadDocumentTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        document_id = args[0]
        document = Document.objects.get(id=document_id)
        document.status = DocumentStatus.COMPLETE
        document.save()
        document.collection.status = CollectionStatus.ACTIVE
        document.collection.save()
        logger.info(f"add qdrant points for document {document.name} success")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        document_id = args[0]
        document = Document.objects.get(id=document_id)
        document.status = DocumentStatus.FAILED
        document.save()
        document.collection.status = CollectionStatus.ACTIVE
        document.collection.save()
        logger.error(f"add qdrant points for document {document.name} error:{exc}")


class CustomDeleteDocumentTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        document_id = args[0]
        document = Document.objects.get(id=document_id)
        logger.info(f"remove qdrant points for document {document.name} success")
        document.status = DocumentStatus.DELETED
        document.gmt_deleted = datetime.now()
        document.save()
        document.collection.status = CollectionStatus.ACTIVE
        document.collection.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        document_id = args[0]
        document = Document.objects.get(id=document_id)
        document.status = DocumentStatus.FAILED
        document.save()
        logger.error(f"remove_index(): index delete from vector db failed:{exc}")

    # def after_return(self, status, retval, task_id, args, kwargs, einfo):
    #     print(retval)
    #     return super(CustomLoadDocumentTask, self).after_return(status, retval, task_id, args, kwargs, einfo)


@app.task(base=CustomLoadDocumentTask, bind=True, ignore_result=True)
def add_index_for_local_document(self, document_id):
    try:
        add_index_for_document(document_id)
    except Exception as e:
        raise self.retry(exc=e, countdown=5, max_retries=3)


@app.task(base=CustomLoadDocumentTask, ignore_result=True, bind=True)
def add_index_for_document(self, document_id, collection_sync_history_id=-1):
    """
        Celery task to do an embedding for a given Document and save the results in vector database.
        Args:
            document_id: the document in Django Module
    """
    if collection_sync_history_id > 0:
        collection_sync_history = CollectionSyncHistory.objects.get(id=collection_sync_history_id)
        collection_sync_history.processing_documents = F("processing_documents") + 1
        collection_sync_history.save()
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    # there is no need to update collection status as it's useless
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()

    try:
        source = get_source(document.collection, json.loads(document.collection.config))
        file_path = source.prepare_document(document)
        loader = LocalPathEmbedding(input_files=[file_path],
                                    vector_store_adaptor=get_vector_db_connector(
                                        collection=generate_qdrant_collection_id(
                                            user=document.user,
                                            collection=document.collection.id)))
        ids = loader.load_data()
        document.relate_ids = ",".join(ids)
        document.save()
        logger.info(f"add qdrant points: {document.relate_ids} for document {file_path}")
        if collection_sync_history_id > 0:
            collection_sync_history.refresh_from_db()
            collection_sync_history.processing_documents = F("processing_documents") - 1
            collection_sync_history.successful_documents = F("successful_documents") + 1
            collection_sync_history.new_documents = F("new_documents") + 1
            collection_sync_history.total_documents = F("total_documents") + 1
            collection_sync_history.save()
            collection_sync_history.update_execution_time()
    except Exception as e:
        if collection_sync_history_id > 0:
            collection_sync_history.refresh_from_db()
            collection_sync_history.processing_documents = F("processing_documents") - 1
            collection_sync_history.failed_documents = F("failed_documents") + 1
            collection_sync_history.save()
            collection_sync_history.update_execution_time()
        raise self.retry(exc=e, countdown=5, max_retries=3)

    source.cleanup_document(file_path, document)


@app.task(base=CustomDeleteDocumentTask, ignore_result=True, bind=True)
def remove_index(self, document_id, collection_sync_history_id = -1):
    """
    remove the doc embedding index from vector store db
    :param self:
    :param document_id:
    """
    if collection_sync_history_id > 0:
        collection_sync_history = CollectionSyncHistory.objects.get(id=collection_sync_history_id)
        collection_sync_history.processing_documents = F("processing_documents") + 1
        collection_sync_history.save()
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()
    try:
        logger.info(f"remove qdrant points: {document.relate_ids} for document {document.file}")
        vector_db = get_vector_db_connector(collection=generate_vector_db_collection_id(user=document.user,
                                                                                        collection=document.collection.id))
        vector_db.connector.delete(ids=str(document.relate_ids).split(','))
        if collection_sync_history_id > 0:
            collection_sync_history.refresh_from_db()
            collection_sync_history.processing_documents = F("processing_documents") - 1
            collection_sync_history.successful_documents = F("successful_documents") + 1
            collection_sync_history.deleted_documents = F("deleted_documents") + 1
            collection_sync_history.total_documents = F("total_documents") + 1
            collection_sync_history.save()
            collection_sync_history.update_execution_time()

    except Exception as e:
        if collection_sync_history_id > 0:
            collection_sync_history.refresh_from_db()
            collection_sync_history.processing_documents = F("processing_documents") - 1
            collection_sync_history.failed_documents = F("failed_documents") + 1
            collection_sync_history.save()
            collection_sync_history.update_execution_time()
        raise self.retry(exc=e, countdown=5, max_retries=3)


@app.task(base=CustomLoadDocumentTask, ignore_result=True, bind=True)
def update_index(self, document_id, collection_sync_history_id=-1):
    if collection_sync_history_id > 0:
        collection_sync_history = CollectionSyncHistory.objects.get(id=collection_sync_history_id)
        collection_sync_history.processing_documents = F("processing_documents") + 1
        collection_sync_history.save()
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()

    try:
        source = get_source(document.collection, json.loads(document.collection.config))
        file_path = source.prepare_document(document)
        loader = LocalPathEmbedding(input_files=[file_path],
                                    vector_store_adaptor=get_vector_db_connector(
                                        collection=generate_qdrant_collection_id(
                                            user=document.user,
                                            collection=document.collection.id)))
        loader.connector.delete(ids=str(document.relate_ids).split(','))
        ids = loader.load_data()
        document.relate_ids = ",".join(ids)
        document.save()
        logger.info(f"update qdrant points: {document.relate_ids} for document {file_path}")
        if collection_sync_history_id > 0:
            collection_sync_history.refresh_from_db()
            collection_sync_history.processing_documents = F("processing_documents") - 1
            collection_sync_history.successful_documents = F("successful_documents") + 1
            collection_sync_history.modified_documents = F("modified_documents") + 1
            collection_sync_history.save()
            collection_sync_history.update_execution_time()
    except Exception as e:
        if collection_sync_history_id > 0:
            collection_sync_history.refresh_from_db()
            collection_sync_history.processing_documents = F("processing_documents") - 1
            collection_sync_history.failed_documents = F("failed_documents") + 1
            collection_sync_history.save()
            collection_sync_history.update_execution_time()
        raise self.retry(exc=e, countdown=5, max_retries=3)
    source.cleanup_document(file_path, document)