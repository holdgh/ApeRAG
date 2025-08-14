# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Synchronous version of DocumentService for use in Celery tasks.
This module provides thread-safe synchronous database operations.
"""

import json
import logging
import os
from typing import List, Dict, Any
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from aperag.config import settings
from aperag.db import models as db_models
from aperag.db.ops import db_ops  # Using sync db_ops
from aperag.docparser.doc_parser import DocParser
from aperag.exceptions import (
    CollectionInactiveException,
    DocumentNotFoundException,
    QuotaExceededException,
    ResourceNotFoundException,
    invalid_param,
)
from aperag.index.manager_sync import document_index_manager_sync
from aperag.objectstore.base import get_object_store
from aperag.schema import view_models
from aperag.utils.uncompress import SUPPORTED_COMPRESSED_EXTENSIONS
from aperag.utils.utils import utc_now

logger = logging.getLogger(__name__)


def _trigger_index_reconciliation():
    """
    Trigger index reconciliation task asynchronously for better real-time responsiveness.

    This is called after document create/update/delete operations to immediately
    process index changes, improving responsiveness compared to relying only on
    periodic reconciliation. The periodic task interval can be increased since
    we have real-time triggering.
    """
    try:
        # Import here to avoid circular dependencies and handle missing celery gracefully
        from config.celery_tasks import reconcile_indexes_task

        # Trigger the reconciliation task asynchronously
        reconcile_indexes_task.delay()
        logger.debug("Index reconciliation task triggered for real-time processing")
    except ImportError:
        logger.warning("Celery not available, skipping index reconciliation trigger")
    except Exception as e:
        logger.warning(f"Failed to trigger index reconciliation task: {e}")


@dataclass
class SyncUploadFile:
    """Simple dataclass to represent an upload file for sync operations"""
    filename: str
    content: bytes
    size: int


class DocumentServiceSync:
    """Synchronous document service for Celery tasks"""

    def __init__(self):
        """Initialize the sync document service"""
        pass

    def _build_document_response(self, document: db_models.Document) -> view_models.Document:
        """
        Build document response object with all index types information.
        """
        # Get all index information if available
        indexes = getattr(
            document, "indexes", {"VECTOR": None, "FULLTEXT": None, "GRAPH": None, "SUMMARY": None, "VISION": None}
        )

        # Parse summary from SUMMARY index's index_data
        summary = None
        summary_index = indexes.get("SUMMARY")
        if summary_index and summary_index.get("index_data"):
            try:
                index_data = json.loads(summary_index["index_data"]) if summary_index["index_data"] else None
                if index_data:
                    summary = index_data.get("summary")
            except Exception:
                summary = None

        return view_models.Document(
            id=document.id,
            name=document.name,
            status=document.status,
            # Vector index information
            vector_index_status=indexes["VECTOR"]["status"] if indexes["VECTOR"] else "SKIPPED",
            vector_index_updated=indexes["VECTOR"]["updated_at"] if indexes["VECTOR"] else None,
            # Fulltext index information
            fulltext_index_status=indexes["FULLTEXT"]["status"] if indexes["FULLTEXT"] else "SKIPPED",
            fulltext_index_updated=indexes["FULLTEXT"]["updated_at"] if indexes["FULLTEXT"] else None,
            # Graph index information
            graph_index_status=indexes["GRAPH"]["status"] if indexes["GRAPH"] else "SKIPPED",
            graph_index_updated=indexes["GRAPH"]["updated_at"] if indexes["GRAPH"] else None,
            # Summary index information
            summary_index_status=indexes["SUMMARY"]["status"] if indexes.get("SUMMARY") else "SKIPPED",
            summary_index_updated=indexes["SUMMARY"]["updated_at"] if indexes.get("SUMMARY") else None,
            vision_index_status=indexes["VISION"]["status"] if indexes.get("VISION") else "SKIPPED",
            vision_index_updated=indexes["VISION"]["updated_at"] if indexes.get("VISION") else None,
            summary=summary,  # Parse from index_data
            size=document.size,
            created=document.gmt_created,
            updated=document.gmt_updated,
        )

    def create_documents(
        self, user: str, collection_id: str, files: List[SyncUploadFile]
    ) -> view_models.DocumentList:
        """
        Synchronous version of create_documents for Celery tasks.
        
        Args:
            user: User ID
            collection_id: Collection ID
            files: List of SyncUploadFile objects
            
        Returns:
            DocumentList with created documents
        """
        if len(files) > 50:
            raise invalid_param("file_count", "documents are too many, add document failed")

        # Check collection exists and is active
        collection = db_ops.query_collection_by_id(collection_id)
        if collection is None or collection.user != user:
            raise ResourceNotFoundException("Collection", collection_id)
        if collection.status != db_models.CollectionStatus.ACTIVE:
            raise CollectionInactiveException(collection_id)

        # Quota checks will be done within the transaction

        supported_file_extensions = DocParser().supported_extensions()
        supported_file_extensions += SUPPORTED_COMPRESSED_EXTENSIONS

        response = []

        # Prepare file data and validate all files before starting any database operations
        file_data = []
        for item in files:
            file_suffix = os.path.splitext(item.filename)[1].lower()
            if file_suffix not in supported_file_extensions:
                raise invalid_param("file_type", f"unsupported file type {file_suffix}")
            if item.size > settings.max_document_size:
                raise invalid_param("file_size", "file size is too large")

            file_data.append(
                {"filename": item.filename, "size": item.size, "suffix": file_suffix, "content": item.content}
            )

        # Process all files in a single transaction for atomicity
        def _create_documents_atomically(session):
            from aperag.db.models import Document, DocumentStatus, UserQuota

            # Check and consume quotas first within the transaction
            # Inline quota check and consume
            stmt = select(UserQuota).where(
                UserQuota.user == user,
                UserQuota.key == "max_document_count"
            )
            result = session.execute(stmt)
            quota = result.scalars().first()
            
            if quota:
                if quota.current_usage + len(files) > quota.quota_limit:
                    raise QuotaExceededException("max_document_count", quota.quota_limit, quota.current_usage)
                quota.current_usage += len(files)
                quota.gmt_updated = utc_now()
                session.add(quota)

            # Check per-collection quota by counting existing documents in this collection
            stmt = (
                select(func.count())
                .select_from(Document)
                .where(Document.collection_id == collection_id, Document.status != DocumentStatus.DELETED)
            )
            existing_doc_count = session.scalar(stmt)

            # Get per-collection quota limit
            stmt = select(UserQuota).where(UserQuota.user == user, UserQuota.key == "max_document_count_per_collection")
            result = session.execute(stmt)
            per_collection_quota = result.scalars().first()

            if per_collection_quota and (existing_doc_count + len(files)) > per_collection_quota.quota_limit:
                raise QuotaExceededException(
                    "max_document_count_per_collection", per_collection_quota.quota_limit, existing_doc_count
                )

            documents_created = []
            obj_store = get_object_store()
            uploaded_files = []  # Track uploaded files for cleanup

            try:
                for file_info in file_data:
                    # Create document in database directly using session
                    document_instance = Document(
                        user=user,
                        name=file_info["filename"],
                        status=DocumentStatus.PENDING,
                        size=file_info["size"],
                        collection_id=collection.id,
                    )
                    session.add(document_instance)
                    session.flush()
                    session.refresh(document_instance)

                    # Upload to object store
                    upload_path = f"{document_instance.object_store_base_path()}/original{file_info['suffix']}"
                    obj_store.put(upload_path, file_info["content"])
                    uploaded_files.append(upload_path)

                    # Update document with object path
                    metadata = json.dumps({"object_path": upload_path})
                    document_instance.doc_metadata = metadata
                    session.add(document_instance)
                    session.flush()
                    session.refresh(document_instance)

                    # Create index specs for the new document
                    index_types = [
                        db_models.DocumentIndexType.VECTOR,
                        db_models.DocumentIndexType.FULLTEXT,
                    ]
                    collection_config = json.loads(collection.config)
                    if collection_config.get("enable_knowledge_graph", False):
                        index_types.append(db_models.DocumentIndexType.GRAPH)

                    if collection_config.get("enable_summary", False):
                        index_types.append(db_models.DocumentIndexType.SUMMARY)

                    if collection_config.get("enable_vision", False):
                        index_types.append(db_models.DocumentIndexType.VISION)

                    # Use index manager to create indexes with new status model
                    document_index_manager_sync.create_or_update_document_indexes(
                        session=session,
                        document_id=document_instance.id,
                        index_types=index_types
                    )

                    # Build response object
                    doc_response = self._build_document_response(document_instance)
                    documents_created.append(doc_response)

                return documents_created

            except Exception as e:
                # Clean up uploaded files on database transaction failure
                for upload_path in uploaded_files:
                    try:
                        obj_store.delete_objects_by_prefix(upload_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup uploaded file during rollback: {cleanup_error}")
                raise e
        
        response = db_ops._execute_transaction(_create_documents_atomically)

        # Trigger index reconciliation after successful document creation
        _trigger_index_reconciliation()

        return view_models.DocumentList(items=response)

    def _delete_document(self, session: Session, user: str, collection_id: str, document_id: str):
        """
        Core logic to delete a single document and its associated resources.
        This method is designed to be called within a transaction.
        """
        # Validate document existence and ownership
        stmt = select(db_models.Document).where(
            db_models.Document.id == document_id,
            db_models.Document.collection_id == collection_id,
            db_models.Document.user == user,
            db_models.Document.status != db_models.DocumentStatus.DELETED
        )
        result = session.execute(stmt)
        document = result.scalars().first()
        
        if document is None:
            # Silently ignore if document not found, as it might have been deleted by another process
            logger.warning(f"Document {document_id} not found for deletion, skipping.")
            return

        # Use index manager to mark all related indexes for deletion
        document_index_manager_sync.delete_document_indexes(
            session=session, 
            document_id=document.id, 
            index_types=None
        )

        # Delete from object store
        obj_store = get_object_store()
        metadata = json.loads(document.doc_metadata) if document.doc_metadata else {}
        if metadata.get("object_path"):
            try:
                # Use delete_objects_by_prefix to remove all related files (original, chunks, etc.)
                obj_store.delete_objects_by_prefix(document.object_store_base_path())
                logger.info(f"Deleted objects from object store with prefix: {document.object_store_base_path()}")
            except Exception as e:
                logger.warning(f"Failed to delete objects for document {document.id} from object store: {e}")

        # Mark document as deleted
        document.status = db_models.DocumentStatus.DELETED
        document.gmt_deleted = utc_now()
        session.add(document)

        # Release quota within the same transaction
        stmt = select(db_models.UserQuota).where(
            db_models.UserQuota.user == user,
            db_models.UserQuota.key == "max_document_count"
        )
        result = session.execute(stmt)
        quota = result.scalars().first()
        
        if quota:
            quota.current_usage = max(0, quota.current_usage - 1)
            session.add(quota)

        session.flush()
        logger.info(f"Successfully marked document {document.id} as deleted.")

        return document

    def delete_document(self, user: str, collection_id: str, document_id: str) -> dict:
        """Delete a single document and trigger index reconciliation."""

        def _delete_document_atomically(session: Session):
            return self._delete_document(session, user, collection_id, document_id)

        result = db_ops._execute_transaction(_delete_document_atomically)

        # Trigger reconciliation to process the deletion
        _trigger_index_reconciliation()
        return result

    def delete_documents(self, user: str, collection_id: str, document_ids: List[str]) -> dict:
        """Delete multiple documents and trigger index reconciliation."""

        def _delete_documents_atomically(session: Session):
            deleted_ids = []
            for doc_id in document_ids:
                self._delete_document(session, user, collection_id, doc_id)
                deleted_ids.append(doc_id)
            return {"deleted_ids": deleted_ids, "status": "success"}

        result = db_ops._execute_transaction(_delete_documents_atomically)

        # Trigger reconciliation to process deletions
        _trigger_index_reconciliation()
        return result


# Create a global sync service instance
document_service_sync = DocumentServiceSync()
