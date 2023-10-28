import json
import logging
import os
import uuid

from celery import Task
from django.utils import timezone

from config.celery import app
from config.vector_db import get_vector_db_connector
from kubechat.llm.predict import Predictor, PredictorType
from kubechat.models import Document, DocumentStatus, MessageFeedback, \
    MessageFeedbackStatus
from kubechat.source.base import get_source
from kubechat.source.feishu.client import FeishuNoPermission, FeishuPermissionDenied
from kubechat.utils.full_text import insert_document, remove_document
from kubechat.utils.utils import generate_vector_db_collection_name, generate_qa_vector_db_collection_name, \
    generate_fulltext_index_name
from readers.base_embedding import get_collection_embedding_model
from readers.local_path_embedding import LocalPathEmbedding
from readers.local_path_qa_embedding import LocalPathQAEmbedding
from readers.qa_embedding import QAEmbedding
from readers.base_readers import DEFAULT_FILE_READER_CLS, FULLTEXT_SUFFIX

logger = logging.getLogger(__name__)


class CustomLoadDocumentTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        document_id = args[0]
        document = Document.objects.get(id=document_id)
        document.status = DocumentStatus.COMPLETE
        document.save()
        logger.info(f"add qdrant points for document {document.name} success")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        document_id = args[0]
        document = Document.objects.get(id=document_id)
        document.status = DocumentStatus.FAILED
        document.save()
        logger.error(f"add qdrant points for document {document.name} error:{exc}")


class CustomDeleteDocumentTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        document_id = args[0]
        document = Document.objects.get(id=document_id)
        logger.info(f"remove qdrant points for document {document.name} success")
        document.status = DocumentStatus.DELETED
        document.gmt_deleted = timezone.now()
        document.name = document.name + "-" + str(uuid.uuid4())
        document.save()

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
        raise self.retry(exc=e, countdown=5, max_retries=1)


@app.task(base=CustomLoadDocumentTask, bind=True, track_started=True)
def add_index_for_document(self, document_id):
    """
        Celery task to do an embedding for a given Document and save the results in vector database.
        Args:
            document_id: the document in Django Module
    """
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()

    try:
        source = get_source(json.loads(document.collection.config))
        metadata = json.loads(document.metadata)
        local_doc = source.prepare_document(name=document.name, metadata=metadata)

        embedding_model, _ = get_collection_embedding_model(document.collection)
        loader = LocalPathEmbedding(input_files=[local_doc.path],
                                    input_file_metadata_list=[local_doc.metadata],
                                    embedding_model=embedding_model,
                                    vector_store_adaptor=get_vector_db_connector(
                                        collection=generate_vector_db_collection_name(
                                            collection_id=document.collection.id)))

        ctx_ids, content = loader.load_data()
        logger.info(f"add ctx qdrant points: {ctx_ids} for document {local_doc.path}")

        # only index the document that have points in the vector database
        if ctx_ids:
            index = generate_fulltext_index_name(document.collection.id)
            insert_document(index, document.id, local_doc.name, content)

        predictor = Predictor.from_model(model_name="baichuan-13b", predictor_type=PredictorType.CUSTOM_LLM)
        qa_loaders = LocalPathQAEmbedding(predictor=predictor,
                                          input_files=[local_doc.path],
                                          input_file_metadata_list=[local_doc.metadata],
                                          embedding_model=embedding_model,
                                          vector_store_adaptor=get_vector_db_connector(
                                              collection=generate_qa_vector_db_collection_name(
                                                  collection=document.collection.id)))
        qa_ids = qa_loaders.load_data()
        logger.info(f"add qa qdrant points: {qa_ids} for document {local_doc.path}")
        relate_ids = {
            "ctx": ctx_ids,
            "qa": qa_ids,
        }
        document.relate_ids = json.dumps(relate_ids)
        document.save()
    except FeishuNoPermission:
        raise Exception("no permission to access document %s" % document.name)
    except FeishuPermissionDenied:
        raise Exception("permission denied to access document %s" % document.name)
    except Exception as e:
        raise e
    source.cleanup_document(local_doc.path)


@app.task(base=CustomDeleteDocumentTask, bind=True, track_started=True)
def remove_index(self, document_id):
    """
    remove the doc embedding index from vector store db
    :param self:
    :param document_id:
    """
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    try:
        index = generate_fulltext_index_name(document.collection.id)
        remove_document(index, document.id)

        relate_ids = json.loads(document.relate_ids)
        vector_db = get_vector_db_connector(
            collection=generate_vector_db_collection_name(collection_id=document.collection.id)
        )
        ctx_relate_ids = relate_ids.get("ctx", [])
        vector_db.connector.delete(ids=ctx_relate_ids)
        logger.info(f"remove ctx qdrant points: {ctx_relate_ids} for document {document.file}")

        qa_vector_db = get_vector_db_connector(
            collection=generate_qa_vector_db_collection_name(collection=document.collection.id))
        qa_relate_ids = relate_ids.get("qa", [])
        qa_vector_db.connector.delete(ids=qa_relate_ids)
        logger.info(f"remove qa qdrant points: {qa_relate_ids} for document {document.file}")

    except Exception as e:
        raise e


@app.task(base=CustomLoadDocumentTask, bind=True, track_started=True)
def update_index(self, document_id):
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()

    try:
        relate_ids = json.loads(document.relate_ids)
        source = get_source(json.loads(document.collection.config))
        metadata = json.loads(document.metadata)
        local_doc = source.prepare_document(name=document.name, metadata=metadata)

        embedding_model, _ = get_collection_embedding_model(document.collection)
        loader = LocalPathEmbedding(input_files=[local_doc.path],
                                    input_file_metadata_list=[local_doc.metadata],
                                    embedding_model=embedding_model,
                                    vector_store_adaptor=get_vector_db_connector(
                                        collection=generate_vector_db_collection_name(
                                            collection_id=document.collection.id)))
        loader.connector.delete(ids=relate_ids.get("ctx", []))
        ctx_ids, content = loader.load_data()
        logger.info(f"add ctx qdrant points: {ctx_ids} for document {local_doc.path}")

        # only index the document that have points in the vector database
        if ctx_ids:
            index = generate_fulltext_index_name(document.collection.id)
            insert_document(index, document.id, local_doc.name, content)

        predictor = Predictor.from_model(model_name="baichuan-13b", predictor_type=PredictorType.CUSTOM_LLM)
        qa_loader = LocalPathQAEmbedding(predictor=predictor,
                                         input_files=[local_doc.path],
                                         input_file_metadata_list=[local_doc.metadata],
                                         embedding_model=embedding_model,
                                         vector_store_adaptor=get_vector_db_connector(
                                             collection=generate_qa_vector_db_collection_name(
                                                 collection=document.collection.id)))
        qa_loader.connector.delete(ids=relate_ids.get("qa", []))
        qa_ids = qa_loader.load_data()
        logger.info(f"add qa qdrant points: {qa_ids} for document {local_doc.path}")
        relate_ids = {
            "ctx": ctx_ids,
            "qa": qa_ids,
        }
        document.relate_ids = json.dumps(relate_ids)
        document.save()
        logger.info(f"update qdrant points: {document.relate_ids} for document {local_doc.path}")
    except FeishuNoPermission:
        raise Exception("no permission to access document %s" % document.name)
    except FeishuPermissionDenied:
        raise Exception("permission denied to access document %s" % document.name)
    except Exception as e:
        logger.error(e)
        raise Exception("an error occur %s" % e)


    source.cleanup_document(local_doc.path)


@app.task
def message_feedback(**kwargs):
    feedback_id = kwargs["feedback_id"]
    feedback = MessageFeedback.objects.get(id=feedback_id)
    feedback.status = MessageFeedbackStatus.RUNNING
    feedback.save()

    qa_collection_name = generate_qa_vector_db_collection_name(collection=feedback.collection.id)
    vector_store_adaptor = get_vector_db_connector(collection=qa_collection_name)
    embedding_model, _ = get_collection_embedding_model(feedback.collection)
    ids = [i for i in str(feedback.relate_ids or "").split(',') if i]
    if ids:
        vector_store_adaptor.connector.delete(ids=ids)
    ids = QAEmbedding(feedback.question, feedback.revised_answer, vector_store_adaptor, embedding_model).load_data()
    if ids:
        feedback.relate_ids = ",".join(ids)
        feedback.save()

    feedback.status = MessageFeedbackStatus.COMPLETE
    feedback.save()
