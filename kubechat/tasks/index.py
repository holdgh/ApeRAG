import json
import logging
import os
import uuid
import zipfile
import tarfile

import py7zr
import rarfile

from celery import Task
from django.utils import timezone
from django.core.files.base import ContentFile
from pathlib import Path
from config.celery import app
from config.vector_db import get_vector_db_connector
from kubechat.llm.base import Predictor, PredictorType
from kubechat.db.models import Document, DocumentStatus, MessageFeedback,Collection,CollectionStatus, \
    MessageFeedbackStatus, ProtectAction
from kubechat.source.base import get_source
from kubechat.source.feishu.client import FeishuNoPermission, FeishuPermissionDenied
from kubechat.context.full_text import insert_document, remove_document
from kubechat.utils.utils import generate_vector_db_collection_name, generate_qa_vector_db_collection_name, \
    generate_fulltext_index_name
from readers.base_readers import DEFAULT_FILE_READER_CLS
from readers.base_embedding import get_collection_embedding_model
from readers.local_path_embedding import LocalPathEmbedding
from readers.local_path_qa_embedding import LocalPathQAEmbedding
from readers.qa_embedding import QAEmbedding
from django.core.files.base import ContentFile
from readers.base_readers import DEFAULT_FILE_READER_CLS, FULLTEXT_SUFFIX, SUPPORTED_COMPRESSED_EXTENSIONS

logger = logging.getLogger(__name__)


class CustomLoadDocumentTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        document_id = args[0]
        document = Document.objects.get(id=document_id)
        if document.status != DocumentStatus.WARNING:
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


class SensitiveInformationFound(Exception):
    """
    raised when Sensitive information found in document
    """


def uncompress_file(document: Document):
    file = Path(document.file.path)
    MAX_EXTRACTED_SIZE = 5000 * 1024 * 1024  # 5 GB
    tmp_dir = Path(os.path.join('/tmp/kubechat', document.collection.id, document.name))
    try:
        os.makedirs(tmp_dir, exist_ok=True)
    except Exception as e:
        raise e
    extracted_files = []

    try:
        if file.suffix == '.zip':
            with zipfile.ZipFile(file, 'r') as zf:
                for name in zf.namelist():
                    try:
                        name_utf8 = name.encode('cp437').decode('utf-8')
                    except:
                        name_utf8 = name
                    zf.extract(name, tmp_dir)
                    if name_utf8 != name:
                        os.rename(os.path.join(tmp_dir, name), os.path.join(tmp_dir, name_utf8))
        elif file.suffix in ['.rar', '.r00']:
            with rarfile.RarFile(file, 'r') as rf:
                rf.extractall(tmp_dir)
        elif file.suffix == '.7z':
            with py7zr.SevenZipFile(file, 'r') as z7:
                z7.extractall(tmp_dir)
        elif file.suffix in ['.tar', '.gz', '.xz', '.bz2', '.tar.gz', '.tar.xz', '.tar.bz2', '.tar.7z']:
            with tarfile.open(file, 'r:*') as tf:
                tf.extractall(tmp_dir)
        else:
            raise ValueError("Unsupported file format")
    except Exception as e:
        raise e
    total_size = 0
    for root, dirs, file_names in os.walk(tmp_dir):
        for name in file_names:
            path = Path(os.path.join(root, name))
            if path.suffix in SUPPORTED_COMPRESSED_EXTENSIONS:
                continue
            if path.suffix not in DEFAULT_FILE_READER_CLS.keys():
                continue
            extracted_files.append(path)
            total_size += path.stat().st_size

            if total_size > MAX_EXTRACTED_SIZE:
                raise Exception("Extracted size exceeded limit")
    for extracted_file_path in extracted_files:
        try:
            with extracted_file_path.open(mode="rb") as extracted_file:  # open in binary
                content = extracted_file.read()
                document_instance = Document(
                    user=document.user,
                    name=document.name + "/" + extracted_file_path.name,
                    status=DocumentStatus.PENDING,
                    size=extracted_file_path.stat().st_size,
                    collection=document.collection,
                    file=ContentFile(content, extracted_file_path.name),
                )
                document_instance.metadata = json.dumps({
                    "path": str(extracted_file_path),
                    "uncompressed": "true"
                })
                document_instance.save()
                add_index_for_local_document.delay(document_instance.id)
        except Exception as e:
            raise e
    return


@app.task(base=CustomLoadDocumentTask, bind=True, ignore_result=True)
def add_index_for_local_document(self, document_id):
    try:
        add_index_for_document(document_id)
    except Exception as e:
        for info in e.args:
            if isinstance(info, str) and "sensitive information" in info:
                raise e
        raise self.retry(exc=e, countdown=5, max_retries=1)


@app.task(base=CustomLoadDocumentTask, bind=True, track_started=True)
def add_index_for_document(self,document_id):
    """
        Celery task to do an embedding for a given Document and save the results in vector database.
        Args:
            document_id: the document in Django Module
    """
    document = Document.objects.get(id=document_id)
    collection =Collection.objects.get(id=document.collection.id)
    if collection.status==CollectionStatus.DELETED:
        return
    document.status = DocumentStatus.RUNNING
    document.save()
    source = None
    local_doc = None
    metadata = json.loads(document.metadata)
    try:
        if document.file and Path(document.file.path).suffix in SUPPORTED_COMPRESSED_EXTENSIONS:
            if json.loads(document.collection.config)["source"] != "system":
                return
            uncompress_file(document)
            return
        else:
            source = get_source(json.loads(document.collection.config))
            local_doc = source.prepare_document(name=document.name, metadata=metadata)
            if document.size == 0:
                document.size = os.path.getsize(local_doc.path)

            embedding_model, _ = get_collection_embedding_model(document.collection)
            loader = LocalPathEmbedding(input_files=[local_doc.path],
                                        input_file_metadata_list=[local_doc.metadata],
                                        embedding_model=embedding_model,
                                        vector_store_adaptor=get_vector_db_connector(
                                            collection=generate_vector_db_collection_name(
                                                collection_id=document.collection.id)))

            config = json.loads(document.collection.config)
            sensitive_protect = config.get("sensitive_protect", False)
            sensitive_protect_method = config.get("sensitive_protect_method", ProtectAction.WARNING_NOT_STORED)
            ctx_ids, content, sensitive_info = loader.load_data(sensitive_protect=sensitive_protect,
                                                                sensitive_protect_method=sensitive_protect_method)
            document.sensitive_info = sensitive_info
            if sensitive_protect and sensitive_info:
                if sensitive_protect_method == ProtectAction.WARNING_NOT_STORED:
                    raise SensitiveInformationFound()
                else:
                    document.status = DocumentStatus.WARNING
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
    except FeishuNoPermission:
        raise Exception("no permission to access document %s" % document.name)
    except FeishuPermissionDenied:
        raise Exception("permission denied to access document %s" % document.name)
    except SensitiveInformationFound:
        raise Exception("sensitive information found in document %s" % document.name)
    except Exception as e:
        raise e
    finally:
        document.save()
        if local_doc and source:
            source.cleanup_document(local_doc.path)
            if "uncompressed" in metadata:
                source.cleanup_document(metadata["path"])


@app.task(base=CustomDeleteDocumentTask, bind=True, track_started=True)
def remove_index(self, document_id):
    """
    remove the doc embedding index from vector store db
    :param self:
    :param document_id:
    """
    document = Document.objects.get(id=document_id)
    try:
        index = generate_fulltext_index_name(document.collection.id)
        remove_document(index, document.id)

        if document.relate_ids == "":
            return

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
    collection =Collection.objects.get(id=document.collection.id)
    if collection.status==CollectionStatus.DELETED:
        return
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

        config = json.loads(document.collection.config)
        sensitive_protect = config.get("sensitive_protect", False)
        sensitive_protect_method = config.get("sensitive_protect_method", ProtectAction.WARNING_NOT_STORED)
        ctx_ids, content, sensitive_info = loader.load_data(sensitive_protect=sensitive_protect,
                                                            sensitive_protect_method=sensitive_protect_method)
        document.sensitive_info = sensitive_info
        if sensitive_protect and sensitive_info != []:
            if sensitive_protect_method == ProtectAction.WARNING_NOT_STORED:
                raise SensitiveInformationFound()
            else:
                document.status = DocumentStatus.WARNING
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
        logger.info(f"update qdrant points: {document.relate_ids} for document {local_doc.path}")
    except FeishuNoPermission:
        raise Exception("no permission to access document %s" % document.name)
    except FeishuPermissionDenied:
        raise Exception("permission denied to access document %s" % document.name)
    except SensitiveInformationFound:
        raise Exception("sensitive information found in document %s" % document.name)
    except Exception as e:
        logger.error(e)
        raise Exception("an error occur %s" % e)
    finally:
        document.save()

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
