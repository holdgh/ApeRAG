"""
LightRAG Stateless Interfaces - Celery Integration Example

This example shows how to use the new stateless interfaces with Celery
to avoid global state conflicts and event loop issues.
"""

import asyncio
from typing import List, Dict, Any
from celery import Celery, Task
from aperag.graph.lightrag import LightRAG
from aperag.config import settings

# Celery app configuration
app = Celery('lightrag_tasks', broker=settings.CELERY_BROKER_URL)


class LightRAGStatelessTask(Task):
    """
    Base task class for LightRAG stateless operations.
    Each worker process maintains its own instances.
    """
    
    _instances: Dict[str, LightRAG] = {}
    
    def get_instance(self, collection_id: str) -> LightRAG:
        """Get or create a LightRAG instance for the collection."""
        if collection_id not in self._instances:
            # Create instance with appropriate configuration
            instance = LightRAG(
                working_dir=f"./lightrag_cache/{collection_id}",
                workspace=collection_id,
                # Important: avoid automatic storage initialization
                auto_manage_storages_states=False,
                # Configure other parameters as needed
                llm_model_func=settings.llm_model_func,
                embedding_func=settings.embedding_func,
            )
            
            # Initialize storages in a controlled manner
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(instance.initialize_storages())
            finally:
                loop.close()
                # Clear event loop to avoid conflicts
                asyncio.set_event_loop(None)
                
            self._instances[collection_id] = instance
            
        return self._instances[collection_id]
    
    def run_async(self, coro):
        """Run async coroutine in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)


@app.task(base=LightRAGStatelessTask, bind=True)
def insert_documents(
    self,
    documents: List[str],
    collection_id: str,
    doc_ids: List[str] = None,
    file_paths: List[str] = None,
) -> Dict[str, Any]:
    """
    Insert documents into LightRAG storage.
    
    This task only writes documents to storage without processing.
    """
    rag = self.get_instance(collection_id)
    
    async def _insert():
        return await rag.ainsert_document(
            documents=documents,
            doc_ids=doc_ids,
            file_paths=file_paths,
        )
    
    return self.run_async(_insert())


@app.task(base=LightRAGStatelessTask, bind=True)
def process_document_chunking(
    self,
    doc_id: str,
    content: str,
    collection_id: str,
    file_path: str = "unknown_source",
    split_by_character: str = None,
) -> Dict[str, Any]:
    """
    Process document chunking.
    
    This task splits a document into chunks and stores them.
    """
    rag = self.get_instance(collection_id)
    
    async def _chunk():
        return await rag.aprocess_chunking(
            doc_id=doc_id,
            content=content,
            file_path=file_path,
            split_by_character=split_by_character,
        )
    
    return self.run_async(_chunk())


@app.task(base=LightRAGStatelessTask, bind=True)
def extract_graph_index(
    self,
    chunks: Dict[str, Any],
    collection_id: str,
) -> Dict[str, Any]:
    """
    Extract entities and relations from chunks and build graph index.
    
    This is the core processing task that performs LLM-based extraction.
    """
    rag = self.get_instance(collection_id)
    
    async def _extract():
        return await rag.aprocess_graph_indexing(
            chunks=chunks,
            collection_id=collection_id,
        )
    
    return self.run_async(_extract())


@app.task(base=LightRAGStatelessTask, bind=True)
def get_document_chunks(
    self,
    doc_id: str,
    collection_id: str,
) -> Dict[str, Any]:
    """
    Get all chunks for a document from storage.
    
    This task retrieves chunks when needed separately.
    """
    rag = self.get_instance(collection_id)
    
    async def _get_chunks():
        chunks = await rag.aget_chunks_by_doc_id(doc_id)
        return {
            "doc_id": doc_id,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }
    
    return self.run_async(_get_chunks())


# ============= Workflow Examples =============

@app.task
def process_document_workflow(
    document: str,
    collection_id: str,
    doc_id: str = None,
    file_path: str = "unknown_source",
) -> Dict[str, Any]:
    """
    Complete workflow for processing a single document.
    
    This chains the stateless tasks together.
    """
    # Step 1: Insert document
    insert_result = insert_documents.apply_async(
        args=[[document], collection_id],
        kwargs={"doc_ids": [doc_id] if doc_id else None, "file_paths": [file_path]}
    ).get()
    
    doc_id = insert_result["doc_ids"][0]
    
    # Step 2: Chunk the document
    chunk_result = process_document_chunking.apply_async(
        args=[doc_id, document, collection_id],
        kwargs={"file_path": file_path}
    ).get()
    
    # Step 3: Extract entities and relations
    # Use the chunks data returned by the chunking task
    chunks = chunk_result.get("chunks_data")
    
    if not chunks:
        # If chunks_data not returned, fetch from storage
        # This would require adding a task to fetch chunks
        return {
            "doc_id": doc_id,
            "status": "error",
            "error": "No chunks data available"
        }
    
    # Extract graph index
    graph_result = extract_graph_index.apply_async(
        args=[chunks, collection_id]
    ).get()
    
    return {
        "doc_id": doc_id,
        "chunks_created": chunk_result["chunk_count"],
        "entities_extracted": graph_result.get("entities_extracted", 0),
        "relations_extracted": graph_result.get("relations_extracted", 0),
        "status": graph_result.get("status", "unknown"),
    }


@app.task
def batch_process_documents(
    documents: List[Dict[str, str]],
    collection_id: str,
) -> List[Dict[str, Any]]:
    """
    Process multiple documents in parallel.
    
    Args:
        documents: List of dicts with 'content', 'doc_id', 'file_path'
        collection_id: Collection identifier
    """
    # Launch parallel workflows
    jobs = []
    for doc in documents:
        job = process_document_workflow.apply_async(
            args=[doc["content"], collection_id],
            kwargs={
                "doc_id": doc.get("doc_id"),
                "file_path": doc.get("file_path", "unknown_source")
            }
        )
        jobs.append(job)
    
    # Collect results
    results = []
    for job in jobs:
        try:
            result = job.get()
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "error": str(e)
            })
    
    return results


# ============= Usage Example =============

if __name__ == "__main__":
    # Example: Process a single document
    result = process_document_workflow.delay(
        document="This is a test document about artificial intelligence and machine learning.",
        collection_id="test_collection",
        file_path="test.txt"
    )
    
    print(f"Task ID: {result.id}")
    print(f"Result: {result.get()}")
    
    # Example: Process multiple documents in parallel
    documents = [
        {
            "content": "Document 1 about AI",
            "doc_id": "doc1",
            "file_path": "doc1.txt"
        },
        {
            "content": "Document 2 about ML",
            "doc_id": "doc2", 
            "file_path": "doc2.txt"
        }
    ]
    
    batch_result = batch_process_documents.delay(
        documents=documents,
        collection_id="test_collection"
    )
    
    print(f"Batch results: {batch_result.get()}") 