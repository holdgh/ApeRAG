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

import json
import logging
import os
from typing import List

from asgiref.sync import sync_to_async
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.config import get_async_session, settings
from aperag.db import models as db_models
from aperag.db.ops import (
    AsyncDatabaseOps,
    async_db_ops,
)
from aperag.docparser.doc_parser import DocParser
from aperag.exceptions import (
    CollectionInactiveException,
    DocumentNotFoundException,
    QuotaExceededException,
    ResourceNotFoundException,
    invalid_param,
)
from aperag.index.manager import document_index_manager
from aperag.objectstore.base import get_object_store
from aperag.schema import view_models
from aperag.schema.view_models import DocumentList
from aperag.utils.constant import QuotaType
from aperag.utils.uncompress import SUPPORTED_COMPRESSED_EXTENSIONS

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


class DocumentService:
    """Document service that handles business logic for documents"""

    def __init__(self, session: AsyncSession = None):
        # Use global db_ops instance by default, or create custom one with provided session
        if session is None:
            self.db_ops = async_db_ops  # Use global instance
        else:
            self.db_ops = AsyncDatabaseOps(session)  # Create custom instance for transaction control

    async def build_document_response(
        self, document: db_models.Document, session: AsyncSession
    ) -> view_models.Document:
        """Build Document response object for API return using new status model."""
        from sqlalchemy import select

        from aperag.db.models import DocumentIndex

        # Get all document indexes for status calculation
        document_indexes = await session.execute(
            select(DocumentIndex).where(
                DocumentIndex.document_id == document.id,
                DocumentIndex.status != db_models.DocumentIndexStatus.DELETING,
                DocumentIndex.status != db_models.DocumentIndexStatus.DELETION_IN_PROGRESS,
            )
        )
        indexes = document_indexes.scalars().all()

        # Map index states to API response format
        index_status = {}
        index_updated = {}

        # Initialize all types as SKIPPED (when no record exists)
        all_types = [
            db_models.DocumentIndexType.VECTOR,
            db_models.DocumentIndexType.FULLTEXT,
            db_models.DocumentIndexType.GRAPH,
        ]
        for index_type in all_types:
            index_status[index_type] = "SKIPPED"

        # Update with actual states from database
        for index in indexes:
            index_status[index.index_type] = index.status
            index_updated[index.index_type] = index.gmt_updated

        return view_models.Document(
            id=document.id,
            name=document.name,
            status=document.status,
            vector_index_status=index_status.get(db_models.DocumentIndexType.VECTOR, "SKIPPED"),
            fulltext_index_status=index_status.get(db_models.DocumentIndexType.FULLTEXT, "SKIPPED"),
            graph_index_status=index_status.get(db_models.DocumentIndexType.GRAPH, "SKIPPED"),
            vector_index_updated=index_updated.get(db_models.DocumentIndexType.VECTOR, None),
            fulltext_index_updated=index_updated.get(db_models.DocumentIndexType.FULLTEXT, None),
            graph_index_updated=index_updated.get(db_models.DocumentIndexType.GRAPH, None),
            size=document.size,
            created=document.gmt_created,
            updated=document.gmt_updated,
        )

    async def create_documents(
        self, user: str, collection_id: str, files: List[UploadFile]
    ) -> view_models.DocumentList:
        if len(files) > 50:
            raise invalid_param("file_count", "documents are too many, add document failed")

        # Check collection exists and is active
        collection = await self.db_ops.query_collection(user, collection_id)
        if collection is None:
            raise ResourceNotFoundException("Collection", collection_id)
        if collection.status != db_models.CollectionStatus.ACTIVE:
            raise CollectionInactiveException(collection_id)

        if settings.max_document_count:
            document_limit = await self.db_ops.query_user_quota(user, QuotaType.MAX_DOCUMENT_COUNT)
            if document_limit is None:
                document_limit = settings.max_document_count
            if await self.db_ops.query_documents_count(user, collection_id) >= document_limit:
                raise QuotaExceededException("document", document_limit)

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

            # Read file content from UploadFile
            file_content = await item.read()
            # Reset file pointer for potential future use
            await item.seek(0)

            file_data.append(
                {"filename": item.filename, "size": item.size, "suffix": file_suffix, "content": file_content}
            )

        # Process all files in a single transaction for atomicity
        async def _create_documents_atomically(session):
            from aperag.db.models import Document, DocumentStatus

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
                    await session.flush()
                    await session.refresh(document_instance)

                    # Upload to object store
                    upload_path = f"{document_instance.object_store_base_path()}/original{file_info['suffix']}"
                    await sync_to_async(obj_store.put)(upload_path, file_info["content"])
                    uploaded_files.append(upload_path)

                    # Update document with object path
                    metadata = json.dumps({"object_path": upload_path})
                    document_instance.doc_metadata = metadata
                    session.add(document_instance)
                    await session.flush()
                    await session.refresh(document_instance)

                    # Create index specs for the new document
                    index_types = [db_models.DocumentIndexType.VECTOR, db_models.DocumentIndexType.FULLTEXT]
                    collection_config = json.loads(collection.config)
                    if collection_config.get("enable_knowledge_graph", False):
                        index_types.append(db_models.DocumentIndexType.GRAPH)

                    # Use index manager to create indexes with new status model
                    await document_index_manager.create_or_update_document_indexes(
                        document_id=document_instance.id, index_types=index_types, session=session
                    )

                    # Build response object
                    doc_response = await self.build_document_response(document_instance, session)
                    documents_created.append(doc_response)

                return documents_created

            except Exception as e:
                # Clean up uploaded files on database transaction failure
                for upload_path in uploaded_files:
                    try:
                        await sync_to_async(obj_store.delete_objects_by_prefix)(upload_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup uploaded file during rollback: {cleanup_error}")
                raise e

        response = await self.db_ops.execute_with_transaction(_create_documents_atomically)

        # Trigger index reconciliation after successful document creation
        _trigger_index_reconciliation()

        return DocumentList(items=response)

    async def list_documents(self, user: str, collection_id: str) -> view_models.DocumentList:
        documents = await self.db_ops.query_documents([user], collection_id)
        response = []
        async for session in get_async_session():
            for document in documents:
                response.append(await self.build_document_response(document, session))
        return DocumentList(items=response)

    async def get_document(self, user: str, collection_id: str, document_id: str) -> view_models.Document:
        document = await self.db_ops.query_document(user, collection_id, document_id)
        if document is None:
            raise DocumentNotFoundException(document_id)
        async for session in get_async_session():
            return await self.build_document_response(document, session)

    async def _delete_document(self, session: AsyncSession, user: str, collection_id: str, document_id: str):
        """
        Core logic to delete a single document and its associated resources.
        This method is designed to be called within a transaction.
        """
        # Validate document existence and ownership
        document = await self.db_ops.query_document(user, collection_id, document_id)
        if document is None:
            # Silently ignore if document not found, as it might have been deleted by another process
            logger.warning(f"Document {document_id} not found for deletion, skipping.")
            return

        # Use index manager to mark all related indexes for deletion
        await document_index_manager.delete_document_indexes(document_id=document.id, index_types=None, session=session)

        # Delete from object store
        obj_store = get_object_store()
        metadata = json.loads(document.doc_metadata) if document.doc_metadata else {}
        if metadata.get("object_path"):
            try:
                # Use delete_objects_by_prefix to remove all related files (original, chunks, etc.)
                await sync_to_async(obj_store.delete_objects_by_prefix)(document.object_store_base_path())
                logger.info(f"Deleted objects from object store with prefix: {document.object_store_base_path()}")
            except Exception as e:
                logger.warning(f"Failed to delete objects for document {document.id} from object store: {e}")

        # Delete the document record from the database
        await session.delete(document)
        await session.flush()
        logger.info(f"Successfully marked document {document.id} and its indexes for deletion.")

        return document

    async def delete_document(self, user: str, collection_id: str, document_id: str) -> dict:
        """Delete a single document and trigger index reconciliation."""

        async def _delete_document_atomically(session: AsyncSession):
            return await self._delete_document(session, user, collection_id, document_id)

        result = await self.db_ops.execute_with_transaction(_delete_document_atomically)

        # Trigger reconciliation to process the deletion
        _trigger_index_reconciliation()
        return result

    async def delete_documents(self, user: str, collection_id: str, document_ids: List[str]) -> dict:
        """Delete multiple documents and trigger index reconciliation."""

        async def _delete_documents_atomically(session: AsyncSession):
            deleted_ids = []
            for doc_id in document_ids:
                await self._delete_document(session, user, collection_id, doc_id)
                deleted_ids.append(doc_id)
            return {"deleted_ids": deleted_ids, "status": "success"}

        result = await self.db_ops.execute_with_transaction(_delete_documents_atomically)

        # Trigger reconciliation to process deletions
        _trigger_index_reconciliation()
        return result

    async def rebuild_document_indexes(
        self, user_id: str, collection_id: str, document_id: str, index_types: List[str]
    ) -> dict:
        """
        Rebuild specified indexes for a document

        Args:
            user_id: User ID
            collection_id: Collection ID
            document_id: Document ID
            index_types: List of index types to rebuild ('VECTOR', 'FULLTEXT', 'GRAPH')

        Returns:
            dict: Success response
        """
        if len(set(index_types)) != len(index_types):
            raise invalid_param("index_types", "duplicate index types are not allowed")

        logger.info(f"Rebuilding indexes for document {document_id} with types: {index_types}")

        # Convert index types to enum values outside transaction
        from aperag.db.models import DocumentIndexType

        index_type_enums = []
        for index_type in index_types:
            if index_type == "VECTOR":
                index_type_enums.append(DocumentIndexType.VECTOR)
            elif index_type == "FULLTEXT":
                index_type_enums.append(DocumentIndexType.FULLTEXT)
            elif index_type == "GRAPH":
                index_type_enums.append(DocumentIndexType.GRAPH)
            else:
                raise invalid_param("index_type", f"Invalid index type: {index_type}")

        # Execute all operations atomically in a single transaction
        async def _rebuild_document_indexes_atomically(session):
            # Verify document exists and user has access
            document = await self.db_ops.query_document(user_id, collection_id, document_id)
            if not document:
                raise DocumentNotFoundException(f"Document {document_id} not found")

            if document.collection_id != collection_id:
                raise ResourceNotFoundException(f"Document {document_id} not found in collection {collection_id}")

            # Verify user has access to the collection
            collection = await self.db_ops.query_collection(user_id, collection_id)
            if not collection or collection.user != user_id:
                raise ResourceNotFoundException(f"Collection {collection_id} not found or access denied")
            collection_config = json.loads(collection.config)
            if not collection_config.get("enable_knowledge_graph", False):
                # Only remove GRAPH type if it's actually in the list to avoid ValueError
                if db_models.DocumentIndexType.GRAPH in index_type_enums:
                    index_type_enums.remove(db_models.DocumentIndexType.GRAPH)

            # Trigger index rebuild by incrementing version for selected index types
            await document_index_manager.create_or_update_document_indexes(session, document_id, index_type_enums)

            logger.info(f"Successfully triggered rebuild for document {document_id} indexes: {index_types}")

            return {"code": "200", "message": f"Index rebuild initiated for types: {', '.join(index_types)}"}

        result = await self.db_ops.execute_with_transaction(_rebuild_document_indexes_atomically)

        # Trigger index reconciliation after successful rebuild initiation
        _trigger_index_reconciliation()

        return result


    async def get_document_content(self, user: str, collection_id: str, document_id: str) -> dict:
        """
        Get document original content from object storage.

        Args:
            user: User ID
            collection_id: Collection ID
            document_id: Document ID

        Returns:
            dict: Document content and metadata
        """
        # Verify document exists and user has access
        document = await self.db_ops.query_document(user, collection_id, document_id)
        if not document:
            raise DocumentNotFoundException(document_id)

        try:
            # Get object store and read content
            obj_store = get_object_store()
            
            # Parse metadata to get object path
            metadata = json.loads(document.doc_metadata) if document.doc_metadata else {}
            object_path = metadata.get("object_path")
            
            if not object_path:
                # Fallback to constructing path
                file_path = f"{document.object_store_base_path()}/original"
                # Try common extensions
                common_extensions = ['.txt', '.md', '.pdf', '.docx', '.doc', '.html', '.json', '.csv']
                content = None
                file_extension = None
                
                for ext in common_extensions:
                    try:
                        test_path = file_path + ext
                        content = await sync_to_async(obj_store.get)(test_path)
                        if content:
                            object_path = test_path
                            file_extension = ext
                            break
                    except Exception:
                        continue
                
                # If no file found with extensions, try without extension
                if not content:
                    try:
                        content = await sync_to_async(obj_store.get)(file_path)
                        object_path = file_path
                    except Exception as e:
                        logger.error(f"Failed to read document content for {document_id}: {str(e)}")
                        raise ResourceNotFoundException("Document content", document_id)
            else:
                # Use stored object path
                try:
                    content = await sync_to_async(obj_store.get)(object_path)
                    # Extract file extension from object path
                    import os
                    file_extension = os.path.splitext(object_path)[1] if object_path else None
                except Exception as e:
                    logger.error(f"Failed to read document content from {object_path} for {document_id}: {str(e)}")
                    raise ResourceNotFoundException("Document content", document_id)

            # Decode content if it's bytes
            if isinstance(content, bytes):
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    # For non-text files, return base64 encoded content
                    import base64
                    content = base64.b64encode(content).decode('utf-8')
                    file_extension = file_extension + "_base64" if file_extension else "base64"

            return {
                "document_id": document_id,
                "name": document.name,
                "content": content,
                "size": document.size,
                "file_extension": file_extension,
                "object_path": object_path,
                "created": document.gmt_created,
                "updated": document.gmt_updated
            }

        except Exception as e:
            logger.error(f"Failed to get document content for {document_id}: {str(e)}")
            if isinstance(e, (DocumentNotFoundException, ResourceNotFoundException)):
                raise e
            raise Exception(f"Failed to get document content: {str(e)}")

    async def get_document_chunks(self, user: str, collection_id: str, document_id: str) -> List[dict]:
        """
        Get document chunks from vector storage.

        Args:
            user: User ID
            collection_id: Collection ID 
            document_id: Document ID

        Returns:
            List[dict]: List of chunks with content and metadata
        """
        # Verify document exists and user has access
        document = await self.db_ops.query_document(user, collection_id, document_id)
        if not document:
            raise DocumentNotFoundException(document_id)

        try:
            # Get collection and chunks in transaction
            async def _get_chunks(session: AsyncSession):
                collection = await document.get_collection(session)
                if not collection:
                    raise ResourceNotFoundException("Collection", collection_id)

                # Get vector index data from DocumentIndex
                from aperag.db.models import DocumentIndex, DocumentIndexType
                from sqlalchemy import select, and_

                stmt = select(DocumentIndex).where(
                    and_(
                        DocumentIndex.document_id == document_id,
                        DocumentIndex.index_type == DocumentIndexType.VECTOR
                    )
                )
                result = await session.execute(stmt)
                doc_index = result.scalar_one_or_none()

                if not doc_index or not doc_index.index_data:
                    logger.warning(f"No vector index found for document {document_id}")
                    return []

                # Parse vector IDs from index data
                try:
                    index_data = json.loads(doc_index.index_data)
                    ctx_ids = index_data.get("context_ids", [])
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Failed to parse index data for document {document_id}: {str(e)}")
                    return []

                if not ctx_ids:
                    logger.warning(f"No context IDs found for document {document_id}")
                    return []

                # Get vector store adaptor and retrieve chunks
                from aperag.utils.utils import generate_vector_db_collection_name
                from config.vector_db import get_vector_db_connector

                vector_store_adaptor = get_vector_db_connector(
                    collection=generate_vector_db_collection_name(collection_id=collection.id)
                )

                # Get chunks from vector store
                chunks = []
                try:
                    # For Qdrant vector store, get documents by IDs
                    if hasattr(vector_store_adaptor.connector, 'client'):
                        # This is Qdrant connector
                        qdrant_client = vector_store_adaptor.connector.client
                        collection_name = vector_store_adaptor.connector.collection_name
                        
                        # Retrieve points by IDs
                        results = qdrant_client.retrieve(
                            collection_name=collection_name,
                            ids=ctx_ids,
                            with_payload=True,
                            with_vectors=True  # Include vectors for display
                        )
                        
                        for i, point in enumerate(results):
                            try:
                                payload = point.payload or {}
                                # Extract content from node_content if it exists
                                node_content = payload.get("_node_content")
                                if node_content:
                                    node_data = json.loads(node_content)
                                    content = node_data.get("text", "No content available")
                                    metadata = node_data.get("metadata", {})
                                else:
                                    content = payload.get("text", "No content available")  
                                    metadata = payload.get("metadata", {})
                                
                                chunk_data = {
                                    "id": str(point.id),
                                    "order": i,
                                    "content": content,
                                    "vector": point.vector if hasattr(point, 'vector') and point.vector else None,
                                    "metadata": {
                                        **metadata,
                                        "source": document.name,
                                        "document_id": document_id,
                                        "chunk_order": i
                                    }
                                }
                                chunks.append(chunk_data)
                            except Exception as e:
                                logger.warning(f"Failed to parse chunk data for {point.id}: {str(e)}")
                                # Fallback with basic info
                                chunks.append({
                                    "id": str(point.id),
                                    "order": i,
                                    "content": f"Chunk {i+1} (ID: {point.id})",
                                    "metadata": {
                                        "source": document.name,
                                        "document_id": document_id,
                                        "chunk_order": i,
                                        "error": "Failed to parse chunk content"
                                    }
                                })
                    else:
                        # Fallback for other vector store types
                        logger.warning(f"Vector store type not supported for chunk retrieval: {type(vector_store_adaptor.connector)}")
                        for i, ctx_id in enumerate(ctx_ids):
                            chunks.append({
                                "id": ctx_id,
                                "order": i,
                                "content": f"Chunk {i+1} content (ID: {ctx_id})",
                                "metadata": {
                                    "source": document.name,
                                    "document_id": document_id,
                                    "chunk_order": i,
                                    "note": "Direct retrieval not implemented for this vector store type"
                                }
                            })
                            
                except Exception as e:
                    logger.error(f"Failed to retrieve chunks from vector store: {str(e)}")
                    # Fallback to basic chunk info
                    for i, ctx_id in enumerate(ctx_ids):
                        chunks.append({
                            "id": ctx_id,
                            "order": i,
                            "content": f"Chunk {i+1} (Error retrieving content)",
                            "metadata": {
                                "source": document.name,
                                "document_id": document_id,
                                "chunk_order": i,
                                "error": str(e)
                            }
                        })

                return chunks

            return await self.db_ops.execute_with_transaction(_get_chunks)

        except Exception as e:
            logger.error(f"Failed to get document chunks for {document_id}: {str(e)}")
            if isinstance(e, (DocumentNotFoundException, ResourceNotFoundException)):
                raise e
            raise Exception(f"Failed to get document chunks: {str(e)}")


# Create a global service instance for easy access
# This uses the global db_ops instance and doesn't require session management in views
document_service = DocumentService()
