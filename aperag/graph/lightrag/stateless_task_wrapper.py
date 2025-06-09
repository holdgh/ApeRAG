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
        1. Inserts the document and processes chunking
        2. Extracts entities and builds graph index
        
        Args:
            content: Document content
            doc_id: Document ID
            file_path: File path for citation
            
        Returns:
            Dict containing processing results
        """
        rag = await self._get_or_create_instance()
        
        try:
            # Step 1 & 2: Insert document and process chunking in one step
            logger.info(f"Inserting and chunking document {doc_id} into LightRAG")
            chunk_result = await rag.ainsert_and_chunk_document(
                documents=[content],
                doc_ids=[doc_id],
                file_paths=[file_path]
            )
            
            # Get results list from the response
            results = chunk_result.get("results", [])
            if not results:
                logger.warning(f"No results returned for document {doc_id}")
                return {
                    "status": "warning",
                    "doc_id": doc_id,
                    "message": "No processing results returned",
                    "chunks_created": 0,
                    "entities_extracted": 0,
                    "relations_extracted": 0
                }
            
            # Process each document result (though typically there's only one for this use case)
            total_chunks_created = 0
            total_entities_extracted = 0
            total_relations_extracted = 0
            processed_docs = []
            
            for doc_result in results:
                doc_result_id = doc_result.get("doc_id")
                chunks_data = doc_result.get("chunks_data", {})
                chunk_count = doc_result.get("chunk_count", 0)
                
                logger.info(f"Processing {chunk_count} chunks for document {doc_result_id}")
                
                if not chunks_data:
                    logger.warning(f"No chunks data returned for document {doc_result_id}")
                    continue
                
                # Step 3: Extract entities and build graph index for this document's chunks
                logger.info(f"Building graph index for document {doc_result_id}")
                graph_result = await rag.aprocess_graph_indexing(
                    chunks=chunks_data,
                    collection_id=str(self.collection.id)
                )
                
                # Accumulate results
                total_chunks_created += chunk_count
                total_entities_extracted += graph_result.get("entities_extracted", 0)
                total_relations_extracted += graph_result.get("relations_extracted", 0)
                
                processed_docs.append({
                    "doc_id": doc_result_id,
                    "chunks_created": chunk_count,
                    "entities_extracted": graph_result.get("entities_extracted", 0),
                    "relations_extracted": graph_result.get("relations_extracted", 0),
                    "graph_status": graph_result.get("status", "unknown")
                })
                
                logger.info(f"Successfully processed document {doc_result_id}: "
                           f"chunks={chunk_count}, entities={graph_result.get('entities_extracted', 0)}, "
                           f"relations={graph_result.get('relations_extracted', 0)}")
            
            # Compile final results
            result = {
                "status": "success",
                "doc_id": doc_id,  # Keep the original requested doc_id
                "total_documents_processed": len(processed_docs),
                "chunks_created": total_chunks_created,
                "entities_extracted": total_entities_extracted,
                "relations_extracted": total_relations_extracted,
                "documents": processed_docs  # Detailed results for each document
            }
            
            logger.info(f"Successfully processed all documents for request {doc_id}: {result}")
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