import os.path
from datetime import datetime
import logging

from celery import Task
from config.celery import app

from config.vector_db import get_vector_db_connector
from readers.local_path_embedding import LocalPathEmbedding
from kubechat.utils.utils import generate_vector_db_collection_id
from kubechat.models import Document, DocumentStatus, CollectionStatus

logger = logging.getLogger(__name__)


def generate_qdrant_collection_id(user, collection) -> str:
    return str(user).replace('|', '-') + "-" + str(collection)


class CustomLoadDocumentTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        print("task successed!")
        return super(CustomLoadDocumentTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print("task failed!")
        return super(CustomLoadDocumentTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        print(retval)
        return super(CustomLoadDocumentTask, self).after_return(status, retval, task_id, args, kwargs, einfo)


@app.task(base=CustomLoadDocumentTask, time_limit=300, soft_time_limit=180)
def add_index_for_document(document_id, file_path):
    """
        Celery task to do an embedding for a given Document and save the results in vector database.
        Args:
            document_id: the document in Django Module
        Returns:
            bool: True if the index is created and saved successfully, False otherwise.
        """
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()
    try:
        loader = LocalPathEmbedding(input_files=[file_path],
                                    vector_store_adaptor=get_vector_db_connector(
                                        collection=generate_qdrant_collection_id(
                                            user=document.user,
                                            collection=document.collection.id)))
        ids = loader.load_data()
        document.relate_ids = ",".join(ids)
        logger.debug(f"add_index_for_document(): add qdrant points: {document.relate_ids}")
    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.save()
        document.collection.status = CollectionStatus.ACTIVE
        document.collection.save()
        logger.error(f"add_index_for_document(): index embedding to vector db failed:{e}")
        return False

    document.status = DocumentStatus.COMPLETE
    document.save()
    document.collection.status = CollectionStatus.ACTIVE
    document.collection.save()
    return True


@app.task
def remove_index(document_id):
    """
    remove the doc embedding index from vector store db

    :param document:
    """
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()
    try:
        logger.debug(f"remove_index(): document id: {document.file.name}")
        logger.debug(f"remove_index(): qdrant points id to delete {document.relate_ids}")
        vector_db = get_vector_db_connector(collection=generate_vector_db_collection_id(user=document.user,
                                                                                        collection=document.collection.id))
        vector_db.connector.delete(ids=str(document.relate_ids).split(','))
    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.save()
        logger.error(f"remove_index(): index delete from vector db failed:{e}")
        return False
    logger.debug(f"remove_index(): index delete from vector db success")
    document.status = DocumentStatus.DELETED
    document.gmt_deleted = datetime.now()
    document.save()
    document.collection.status = CollectionStatus.ACTIVE
    document.collection.save()


@app.task
def update_index(document_id, file_path):
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()

    try:
        loader = LocalPathEmbedding(input_files=[file_path],
                                    vector_store_adaptor=get_vector_db_connector(
                                        collection=generate_qdrant_collection_id(
                                            user=document.user,
                                            collection=document.collection.id)))
        loader.connector.delete(ids=str(document.relate_ids).split(','))
        ids = loader.load_data()
        document.relate_ids = ",".join(ids)
        logger.debug(f"add_index_for_document(): add qdrant points: {document.relate_ids}")

    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.save()
        logger.error(f"updata_index(): index delete from vector db failed:{e}")
        return False
