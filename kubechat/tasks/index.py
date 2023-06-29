from datetime import datetime
import logging

from celery import Task
from config.celery import app

from config.settings import VECTOR_DB_TYPE
from config.vector_db import get_local_vector_db_connector
from readers.local_path_embedding import LocalPathEmbedding
from kubechat.utils.utils import generate_vector_db_collection_id

from kubechat.models import Document, DocumentStatus

status = DocumentStatus
logger = logging.getLogger(__name__)


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


@app.task(base=CustomLoadDocumentTask)
def add_index_for_document(document_id) -> bool:
    """
        Celery task to create a GPTSimpleVectorIndex for a given Document

        This task takes the ID of a Document object and check the Document status
        Then, it creates a GPTSimpleVectorIndex using
        the provided code and saves the index to the Comparison.model FileField.

        Args:


        Returns:
            bool: True if the index is created and saved successfully, False otherwise.
        """
    document = Document.objects.get(id=document_id)
    document.status = status.RUNNING
    document.save()
    try:
        loader = LocalPathEmbedding(input_files=[document.file.name], embedding_config={"model_type": "huggingface"},
                                    vector_store_adaptor=get_local_vector_db_connector(VECTOR_DB_TYPE,
                                                                                       collection=generate_vector_db_collection_id(
                                                                                           user=document.user,
                                                                                           collection=document.collection.id)))
        ids = loader.load_data()
        document.relate_ids = ",".join(ids)
    except Exception as e:
        document.status = status.FAILED
        document.save()
        logger.error(f"index embedding to vector db failed:{e}")
        return False

    document.status = status.COMPLETE
    document.save()
    return True


@app.task
def remove_index(document_id) -> bool:
    """
    remove the doc embedding index from vector store db
    :param doc:
    :return:
    """
    document = Document.objects.get(id=document_id)
    document.status = status.RUNNING
    document.save()

    try:
        logger.debug(f"document id: {document.file.name}")
        logger.debug(f"qdrant points id to delete {document.relate_ids}")
        vector_db = get_local_vector_db_connector(VECTOR_DB_TYPE,
                                                  collection=generate_vector_db_collection_id(user=document.user,
                                                                                              collection=document.collection.id))
        vector_db.connector.delete(ids=str(document.relate_ids).split(','))
        document.status = DocumentStatus.DELETED
        document.gmt_deleted = datetime.now()
        document.save()
        logger.debug(f"index delete from vector db success")
    except Exception as e:
        document.status = status.FAILED
        document.save()
        logger.error(f"index delete from vector db failed:{e}")
        return False
