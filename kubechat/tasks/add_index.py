import logging
from typing import Optional

from config.celery import app
from langchain.llms import FakeListLLM
from llama_index import SimpleDirectoryReader, StorageContext, ServiceContext

from config.vector_db import vector_db_connector
from kubechat.models import Document, DocumentStatus
from llama_index import VectorStoreIndex, download_loader
from llama_index.readers.schema.base import Document as lla_doc
from celery import Task

from readers.local_path_embedding import LocalPathEmbedding
from vectorstore.base import VectorStoreConnector

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
        loader = LocalPathEmbedding(input_dir=document.file.name, embedding_config={"model_type": "huggingface"},
                                    vector_store_adaptor=vector_db_connector)
        loader.load_data()
    except Exception as e:
        document.status = status.FAILED
        document.save()
        logger.error(f"index embedding to vector db failed:{e}")
        return False

    document.status = status.COMPLETE
    document.save()
    return True


def persistent_in_vector_db(document, vector_store_db: Optional[VectorStoreConnector] = None) -> bool:
    """
    persistent the document in the vector db
    :param vector_store_db: vector store conn
    :param document:
    :return
    """
    if vector_store_db is None:
        return False
    storage_context = StorageContext.from_defaults(vector_store=vector_store_db.store)
    service_context = ServiceContext.from_defaults(
        chunk_size=2048,
        chunk_overlap=200,
        llm=FakeListLLM(responses=["fake"]),
    )
    VectorStoreIndex.from_documents(
        document, service_context=service_context, storage_context=storage_context
    )
    return True


@app.task
def remove_index(doc):
    """
    remove the doc embedding index from vector store db
    :param doc:
    :return:
    """
    if doc.status == status.DELETED:
        pass
    doc.status = status.RUNNING
    loader = SimpleDirectoryReader(
        doc, recursive=True, exclude_hidden=False
    )
    documents = loader.load_data()
