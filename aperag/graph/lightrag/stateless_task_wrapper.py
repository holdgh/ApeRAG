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

import asyncio
import logging
from typing import Dict, Any, Optional
from aperag.graph.lightrag import LightRAG
from aperag.db.models import Collection

logger = logging.getLogger(__name__)


class StatelessLightRAGWrapper:
    """
    A wrapper for using stateless LightRAG interfaces in Celery tasks.
    This wrapper handles event loop management and provides clean async execution.
    """
    
    def __init__(self, collection: Collection, use_cache: bool = False):
        """
        Initialize the wrapper with collection configuration.
        
        Args:
            collection: The collection configuration
            use_cache: Whether to use instance caching (default False for Celery)
        """
        self.collection = collection
        self.use_cache = use_cache
        self._rag_instance: Optional[LightRAG] = None
        
    async def _get_or_create_instance(self) -> LightRAG:
        """Get or create a LightRAG instance for this wrapper."""
        if self._rag_instance is None:
            # Import here to avoid circular imports
            from aperag.graph.lightrag_holder import get_lightrag_holder
            
            # Get a LightRAG holder without caching for Celery tasks
            rag_holder = await get_lightrag_holder(self.collection, use_cache=self.use_cache)
            self._rag_instance = rag_holder.rag
            
        return self._rag_instance
    
    async def process_document_async(
        self, 
        content: str, 
        doc_id: str, 
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process a document using the new stateless interfaces.
        
        This method:
        1. Inserts the document
        2. Processes chunking
        3. Extracts entities and builds graph index
        
        Args:
            content: Document content
            doc_id: Document ID
            file_path: File path for citation
            
        Returns:
            Dict containing processing results
        """
        rag = await self._get_or_create_instance()
        
        try:
            # # Step 1: Insert document
            # logger.info(f"Inserting document {doc_id} into LightRAG")
            # insert_result = await rag.ainsert_document(
            #     documents=[content],
            #     doc_ids=[doc_id],
            #     file_paths=[file_path]
            # )
            #
            # # Verify document was inserted
            # inserted_doc_id = insert_result["doc_ids"][0]
            # if str(inserted_doc_id) != str(doc_id):
            #     logger.warning(f"Document ID mismatch: expected {doc_id}, got {inserted_doc_id}")
            #
            # # Step 2: Process chunking
            # logger.info(f"Processing chunks for document {doc_id}")
            # chunk_result = await rag.aprocess_chunking(
            #     doc_id=str(doc_id),
            #     content=content,
            #     file_path=file_path
            # )

            chunk_result = await rag.ainsert_and_chunk_document(
                documents=[content],
                doc_ids=[doc_id],
                file_paths=[file_path]
            )
            
            # Step 3: Extract entities and build graph index
            logger.info(f"Building graph index for document {doc_id}")
            chunks_data = chunk_result.get("chunks_data", {})
            
            if not chunks_data:
                logger.warning(f"No chunks data returned for document {doc_id}")
                return {
                    "status": "warning",
                    "doc_id": doc_id,
                    "message": "No chunks generated",
                    "chunks_created": 0,
                    "entities_extracted": 0,
                    "relations_extracted": 0
                }
            
            graph_result = await rag.aprocess_graph_indexing(
                chunks=chunks_data,
                collection_id=str(self.collection.id)
            )
            
            # Compile results
            result = {
                "status": "success",
                "doc_id": doc_id,
                "chunks_created": chunk_result.get("chunk_count", 0),
                "entities_extracted": graph_result.get("entities_extracted", 0),
                "relations_extracted": graph_result.get("relations_extracted", 0),
                "processing_status": graph_result.get("status", "unknown")
            }
            
            logger.info(f"Successfully processed document {doc_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {str(e)}")
            raise
    
    def process_document_sync(
        self, 
        content: str, 
        doc_id: str, 
        file_path: str
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for process_document_async.
        Creates a new event loop to avoid conflicts with Celery.
        
        Args:
            content: Document content
            doc_id: Document ID
            file_path: File path for citation
            
        Returns:
            Dict containing processing results
        """
        # Create a new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async method in the new loop
            result = loop.run_until_complete(
                self.process_document_async(content, doc_id, file_path)
            )
            return result
        finally:
            # Clean up the event loop
            loop.close()
            asyncio.set_event_loop(None)
    
    async def delete_document_async(self, doc_id: str) -> Dict[str, Any]:
        """
        Delete a document from LightRAG using stateless interface.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            Dict containing deletion status
        """
        rag = await self._get_or_create_instance()
        
        try:
            logger.info(f"Deleting document {doc_id} from LightRAG")
            await rag.adelete_by_doc_id(str(doc_id))
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "message": "Document deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            raise
    
    def delete_document_sync(self, doc_id: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for delete_document_async.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            Dict containing deletion status
        """
        # Create a new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async method in the new loop
            result = loop.run_until_complete(
                self.delete_document_async(doc_id)
            )
            return result
        finally:
            # Clean up the event loop
            loop.close()
            asyncio.set_event_loop(None)


def process_document_for_celery(
    collection: Collection,
    content: str,
    doc_id: str,
    file_path: str
) -> Dict[str, Any]:
    """
    Convenience function for Celery tasks to process a document.
    
    This function creates a StatelessLightRAGWrapper and processes
    the document using the new stateless interfaces.
    
    Args:
        collection: Collection configuration
        content: Document content
        doc_id: Document ID
        file_path: File path for citation
        
    Returns:
        Dict containing processing results
    """
    wrapper = StatelessLightRAGWrapper(collection, use_cache=False)
    return wrapper.process_document_sync(content, doc_id, file_path)


def delete_document_for_celery(
    collection: Collection,
    doc_id: str
) -> Dict[str, Any]:
    """
    Convenience function for Celery tasks to delete a document.
    
    Args:
        collection: Collection configuration
        doc_id: Document ID to delete
        
    Returns:
        Dict containing deletion status
    """
    wrapper = StatelessLightRAGWrapper(collection, use_cache=False)
    return wrapper.delete_document_sync(doc_id) 