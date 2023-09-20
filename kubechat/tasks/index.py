import json
import logging
import uuid

from celery import Task
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from config import settings
from config.celery import app
from config.vector_db import get_vector_db_connector
from kubechat.llm.predict import Predictor, PredictorType
from kubechat.models import Document, DocumentStatus, CollectionStatus, CollectionSyncHistory, MessageFeedback, \
    MessageFeedbackStatus
from kubechat.source.base import get_source
from kubechat.source.utils import FeishuNoPermission, FeishuPermissionDenied
from kubechat.utils.full_text import insert_document, remove_document
from kubechat.utils.utils import generate_vector_db_collection_name, generate_qa_vector_db_collection_name, \
    generate_fulltext_index_name
from readers.base_embedding import get_collection_embedding_model
from readers.local_path_embedding import LocalPathEmbedding
from readers.local_path_qa_embedding import LocalPathQAEmbedding
from readers.qa_embedding import QAEmbedding

logger = logging.getLogger(__name__)


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
        document.gmt_deleted = timezone.now()
        document.name = document.name + "-" + str(uuid.uuid4())
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
        raise self.retry(exc=e, countdown=5, max_retries=1)


def start_sync_task(collection_sync_history_id):
    with transaction.atomic():
        CollectionSyncHistory.objects.select_for_update(nowait=False).get(id=collection_sync_history_id)
        CollectionSyncHistory.objects.filter(id=collection_sync_history_id).update(
            processing_documents=F("processing_documents") + 1)


def deal_sync_task_success(collection_sync_history_id, task_type: str):
    with transaction.atomic():
        collection_sync_history = CollectionSyncHistory.objects.select_for_update(nowait=False).get(
            id=collection_sync_history_id)
        CollectionSyncHistory.objects.filter(id=collection_sync_history_id).update(
            processing_documents=F("processing_documents") - 1,
            successful_documents=F("successful_documents") + 1
        )
        if task_type == "add":
            CollectionSyncHistory.objects.filter(id=collection_sync_history_id).update(
                new_documents=F("new_documents") + 1, total_documents=F("total_documents") + 1)
        elif task_type == "remove":
            CollectionSyncHistory.objects.filter(id=collection_sync_history_id).update(
                deleted_documents=F("deleted_documents") + 1, total_documents=F("total_documents") - 1)
        elif task_type == "update":
            CollectionSyncHistory.objects.filter(id=collection_sync_history_id).update(
                modified_documents=F("modified_documents") + 1)
        collection_sync_history.update_execution_time()


def deal_sync_task_failure(collection_sync_history_id):
    with transaction.atomic():
        collection_sync_history = CollectionSyncHistory.objects.select_for_update(nowait=False).get(
            id=collection_sync_history_id)
        CollectionSyncHistory.objects.filter(id=collection_sync_history_id).update(
            processing_documents=F("processing_documents") - 1, failed_documents=F("failed_documents") + 1)
        collection_sync_history.update_execution_time()


@app.task(base=CustomLoadDocumentTask, ignore_result=True, bind=True)
def add_index_for_document(self, document_id, collection_sync_history_id=-1):
    """
        Celery task to do an embedding for a given Document and save the results in vector database.
        Args:
            document_id: the document in Django Module
    """
    if collection_sync_history_id > 0:
        start_sync_task(collection_sync_history_id)
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    # there is no need to update collection status as it's useless
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()

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
                                            user=document.user,
                                            collection=document.collection.id)))

        ctx_ids = loader.load_data()
        logger.info(f"add ctx qdrant points: {ctx_ids} for document {local_doc.path}")

        # only index the document that have points in the vector database
        if ctx_ids:
            with open(local_doc.path) as fd:
                doc_content = fd.read()

            index = generate_fulltext_index_name(document.user, document.collection.id)
            insert_document(index, document.id, local_doc.name, doc_content)

        predictor = Predictor.from_model(model_name="baichuan-13b", predictor_type=PredictorType.CUSTOM_LLM)
        qa_loaders = LocalPathQAEmbedding(predictor=predictor,
                                          input_files=[local_doc.path],
                                          input_file_metadata_list=[local_doc.metadata],
                                          embedding_model=embedding_model,
                                          vector_store_adaptor=get_vector_db_connector(
                                              collection=generate_qa_vector_db_collection_name(
                                                  user=document.user,
                                                  collection=document.collection.id)))
        qa_ids = qa_loaders.load_data()
        logger.info(f"add qa qdrant points: {qa_ids} for document {local_doc.path}")
        relate_ids = {
            "ctx": ctx_ids,
            "qa": qa_ids,
        }
        document.relate_ids = json.dumps(relate_ids)
        document.save()

        if collection_sync_history_id > 0:
            deal_sync_task_success(collection_sync_history_id, "add")
    except FeishuNoPermission:
        raise Exception("no permission to access document %s" % document.name)
    except FeishuPermissionDenied:
        raise Exception("permission denied to access document %s" % document.name)
    except Exception as e:
        logger.error(e)
        if collection_sync_history_id > 0:
            deal_sync_task_failure(collection_sync_history_id)
        raise self.retry(exc=e, countdown=5, max_retries=1)

    source.cleanup_document(local_doc.path)


@app.task(base=CustomDeleteDocumentTask, ignore_result=True, bind=True)
def remove_index(self, document_id, collection_sync_history_id=-1):
    """
    remove the doc embedding index from vector store db
    :param self:
    :param document_id:
    """
    if collection_sync_history_id > 0:
        start_sync_task(collection_sync_history_id)
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()
    try:
        index = generate_fulltext_index_name(document.user, document.collection.id)
        remove_document(index, document.id)

        relate_ids = json.loads(document.relate_ids)
        vector_db = get_vector_db_connector(collection=generate_vector_db_collection_name(user=document.user,
                                                                                          collection=document.collection.id))
        ctx_relate_ids = relate_ids.get("ctx", [])
        vector_db.connector.delete(ids=ctx_relate_ids)
        logger.info(f"remove ctx qdrant points: {ctx_relate_ids} for document {document.file}")

        qa_vector_db = get_vector_db_connector(collection=generate_qa_vector_db_collection_name(user=document.user,
                                                                                          collection=document.collection.id))
        qa_relate_ids = relate_ids.get("qa", [])
        qa_vector_db.connector.delete(ids=qa_relate_ids)
        logger.info(f"remove qa qdrant points: {qa_relate_ids} for document {document.file}")

        if collection_sync_history_id > 0:
            deal_sync_task_success(collection_sync_history_id, "remove")
    except Exception as e:
        logger.error(e)
        if collection_sync_history_id > 0:
            deal_sync_task_failure(collection_sync_history_id)
        # raise self.retry(exc=e, countdown=5, max_retries=3)


@app.task(base=CustomLoadDocumentTask, ignore_result=True, bind=True)
def update_index(self, document_id, collection_sync_history_id=-1):
    if collection_sync_history_id > 0:
        start_sync_task(collection_sync_history_id)
    document = Document.objects.get(id=document_id)
    document.status = DocumentStatus.RUNNING
    document.save()
    document.collection.status = CollectionStatus.INACTIVE
    document.collection.save()

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
                                            user=document.user,
                                            collection=document.collection.id)))
        loader.connector.delete(ids=relate_ids.get("ctx", []))
        ctx_ids = loader.load_data()
        logger.info(f"add ctx qdrant points: {ctx_ids} for document {local_doc.path}")

        # only index the document that have points in the vector database
        if ctx_ids:
            with open(local_doc.path) as fd:
                doc_content = fd.read()
            index = generate_fulltext_index_name(document.user, document.collection.id)
            insert_document(index, document.id, local_doc.name, doc_content)

        predictor = Predictor.from_model(model_name="baichuan-13b", predictor_type=PredictorType.CUSTOM_LLM)
        qa_loader = LocalPathQAEmbedding(predictor=predictor,
                                          input_files=[local_doc.path],
                                          input_file_metadata_list=[local_doc.metadata],
                                          embedding_model=embedding_model,
                                          vector_store_adaptor=get_vector_db_connector(
                                              collection=generate_qa_vector_db_collection_name(
                                                  user=document.user,
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
        if collection_sync_history_id > 0:
            deal_sync_task_success(collection_sync_history_id, "update")
    except FeishuNoPermission:
        raise Exception("no permission to access document %s" % document.name)
    except FeishuPermissionDenied:
        raise Exception("permission denied to access document %s" % document.name)
    except Exception as e:
        logger.error(e)
        if collection_sync_history_id > 0:
            deal_sync_task_failure(collection_sync_history_id)
        raise self.retry(exc=e, countdown=5, max_retries=1)
    source.cleanup_document(local_doc.path)


@app.task
def message_feedback(**kwargs):
    feedback_id = kwargs["feedback_id"]
    feedback = MessageFeedback.objects.get(id=feedback_id)
    feedback.status = MessageFeedbackStatus.RUNNING
    feedback.save()

    qa_collection_name = generate_qa_vector_db_collection_name(user=feedback.user, collection=feedback.collection.id)
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
