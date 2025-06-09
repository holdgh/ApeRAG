"""
Test script for LightRAG stateless interfaces

This script demonstrates the usage of new stateless interfaces and
verifies that they can work concurrently without global state conflicts.
"""

import asyncio
import time
from typing import List, Dict, Any
from aperag.graph.lightrag import LightRAG
from aperag.config import settings


async def test_stateless_document_processing():
    """Test basic stateless document processing workflow"""
    
    # Create LightRAG instance
    rag = LightRAG(
        working_dir="./test_lightrag_cache",
        workspace="test_collection",
        llm_model_func=settings.llm_model_func,
        embedding_func=settings.embedding_func,
    )
    
    # Initialize storages
    await rag.initialize_storages()
    
    # Test document
    test_doc = """
    Artificial Intelligence (AI) is transforming the technology industry.
    Companies like Google, Microsoft, and OpenAI are leading the AI revolution.
    Machine learning and deep learning are key technologies in AI development.
    """
    
    print("=== Testing Stateless Document Processing ===")
    
    # Step 1: Insert document
    print("\n1. Inserting document...")
    insert_result = await rag.ainsert_document(
        documents=[test_doc],
        file_paths=["test_ai.txt"]
    )
    doc_id = insert_result["doc_ids"][0]
    print(f"Document inserted with ID: {doc_id}")
    
    # Step 2: Process chunking
    print("\n2. Processing chunks...")
    chunk_result = await rag.aprocess_chunking(
        doc_id=doc_id,
        content=test_doc,
        file_path="test_ai.txt"
    )
    print(f"Created {chunk_result['chunk_count']} chunks")
    
    # Step 3: Extract graph index
    print("\n3. Extracting entities and relations...")
    chunks = chunk_result["chunks_data"]
    graph_result = await rag.aprocess_graph_indexing(
        chunks=chunks,
        collection_id="test_collection"
    )
    print(f"Extracted {graph_result['entities_extracted']} entities")
    print(f"Extracted {graph_result['relations_extracted']} relations")
    
    # Finalize storages
    await rag.finalize_storages()
    
    return graph_result


async def test_concurrent_processing():
    """Test concurrent processing of multiple collections"""
    
    print("\n=== Testing Concurrent Processing ===")
    
    # Test documents for different collections
    documents = {
        "tech_collection": """
        Apple Inc. is a technology company founded by Steve Jobs.
        The iPhone revolutionized mobile computing.
        Tim Cook is the current CEO of Apple.
        """,
        "science_collection": """
        Albert Einstein developed the theory of relativity.
        Quantum mechanics is a fundamental theory in physics.
        Marie Curie was a pioneering scientist in radioactivity research.
        """,
        "business_collection": """
        Amazon was founded by Jeff Bezos in 1994.
        E-commerce has transformed retail business globally.
        AWS is Amazon's cloud computing platform.
        """
    }
    
    async def process_collection(collection_id: str, content: str):
        """Process a single collection"""
        start_time = time.time()
        
        # Create separate LightRAG instance for each collection
        rag = LightRAG(
            working_dir=f"./test_cache_{collection_id}",
            workspace=collection_id,
            llm_model_func=settings.llm_model_func,
            embedding_func=settings.embedding_func,
        )
        
        await rag.initialize_storages()
        
        try:
            # Insert document
            insert_result = await rag.ainsert_document(
                documents=[content],
                file_paths=[f"{collection_id}.txt"]
            )
            doc_id = insert_result["doc_ids"][0]
            
            # Process chunks
            chunk_result = await rag.aprocess_chunking(
                doc_id=doc_id,
                content=content,
                file_path=f"{collection_id}.txt"
            )
            
            # Extract graph index
            chunks = chunk_result["chunks_data"]
            graph_result = await rag.aprocess_graph_indexing(
                chunks=chunks,
                collection_id=collection_id
            )
            
            elapsed_time = time.time() - start_time
            
            print(f"\n{collection_id} completed in {elapsed_time:.2f}s:")
            print(f"  - Entities: {graph_result['entities_extracted']}")
            print(f"  - Relations: {graph_result['relations_extracted']}")
            
            return {
                "collection_id": collection_id,
                "elapsed_time": elapsed_time,
                "result": graph_result
            }
            
        finally:
            await rag.finalize_storages()
    
    # Process all collections concurrently
    start_total = time.time()
    tasks = [
        process_collection(collection_id, content)
        for collection_id, content in documents.items()
    ]
    
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_total
    
    print(f"\nTotal concurrent processing time: {total_time:.2f}s")
    print(f"Average time per collection: {total_time/len(documents):.2f}s")
    
    # If this were using the old global state, collections would process sequentially
    # and total time would be approximately sum of individual times
    sequential_estimate = sum(r["elapsed_time"] for r in results)
    print(f"Estimated sequential time: {sequential_estimate:.2f}s")
    print(f"Speedup: {sequential_estimate/total_time:.2f}x")
    
    return results


async def test_incremental_processing():
    """Test incremental processing - adding chunks to existing collection"""
    
    print("\n=== Testing Incremental Processing ===")
    
    rag = LightRAG(
        working_dir="./test_incremental_cache",
        workspace="incremental_collection",
        llm_model_func=settings.llm_model_func,
        embedding_func=settings.embedding_func,
    )
    
    await rag.initialize_storages()
    
    # First batch of documents
    doc1 = "Python is a popular programming language created by Guido van Rossum."
    
    # Insert and process first document
    result1 = await rag.ainsert_document([doc1], file_paths=["python.txt"])
    doc_id1 = result1["doc_ids"][0]
    
    chunk_result1 = await rag.aprocess_chunking(doc_id1, doc1, "python.txt")
    graph_result1 = await rag.aprocess_graph_indexing(
        chunk_result1["chunks_data"],
        "incremental_collection"
    )
    
    print(f"First document - Entities: {graph_result1['entities_extracted']}")
    
    # Second batch - different document, same collection
    doc2 = "JavaScript is the language of the web, created by Brendan Eich."
    
    result2 = await rag.ainsert_document([doc2], file_paths=["javascript.txt"])
    doc_id2 = result2["doc_ids"][0]
    
    chunk_result2 = await rag.aprocess_chunking(doc_id2, doc2, "javascript.txt")
    graph_result2 = await rag.aprocess_graph_indexing(
        chunk_result2["chunks_data"],
        "incremental_collection"
    )
    
    print(f"Second document - Entities: {graph_result2['entities_extracted']}")
    
    # Check total entities in the collection
    all_labels = await rag.get_graph_labels()
    print(f"\nTotal entities in collection: {len(all_labels)}")
    print(f"Entity labels: {all_labels}")
    
    await rag.finalize_storages()
    
    return all_labels


async def test_chunk_retrieval():
    """Test chunk retrieval functionality"""
    
    print("\n=== Testing Chunk Retrieval ===")
    
    rag = LightRAG(
        working_dir="./test_retrieval_cache",
        workspace="retrieval_collection",
        llm_model_func=settings.llm_model_func,
        embedding_func=settings.embedding_func,
    )
    
    await rag.initialize_storages()
    
    # Insert a document
    doc = "Natural Language Processing (NLP) enables computers to understand human language."
    result = await rag.ainsert_document([doc], file_paths=["nlp.txt"])
    doc_id = result["doc_ids"][0]
    
    # Process chunks
    chunk_result = await rag.aprocess_chunking(doc_id, doc, "nlp.txt")
    chunk_ids = chunk_result["chunks"]
    
    print(f"Created chunks: {chunk_ids}")
    
    # Test retrieving chunks by document ID
    doc_chunks = await rag.aget_chunks_by_doc_id(doc_id)
    print(f"\nRetrieved {len(doc_chunks)} chunks by doc_id")
    
    # Test retrieving specific chunks by IDs
    if chunk_ids:
        specific_chunks = await rag.aget_chunks_by_ids(chunk_ids[:1])
        print(f"Retrieved {len(specific_chunks)} specific chunks")
        for chunk_id, chunk_data in specific_chunks.items():
            print(f"  Chunk {chunk_id}: {chunk_data['content'][:50]}...")
    
    await rag.finalize_storages()
    
    return doc_chunks


async def main():
    """Run all tests"""
    
    print("Starting LightRAG Stateless Interface Tests\n")
    
    # Test 1: Basic workflow
    await test_stateless_document_processing()
    
    # Test 2: Concurrent processing
    await test_concurrent_processing()
    
    # Test 3: Incremental processing
    await test_incremental_processing()
    
    # Test 4: Chunk retrieval
    await test_chunk_retrieval()
    
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 