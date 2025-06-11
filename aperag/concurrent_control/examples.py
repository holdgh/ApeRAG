"""
Usage examples for the universal concurrent control module.

This file demonstrates various ways to use the concurrent control system
in different scenarios and deployment environments.
"""

import asyncio
import logging
from typing import List

from aperag.concurrent_control import (
    create_lock,
    ThreadingLock,
    LockManager,
    lock_context,
    get_default_lock_manager
)

# Configure logging for examples
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_threading_lock():
    """
    Example 1: Basic threading lock usage
    """
    print("\n=== Example 1: Basic Threading Lock ===")
    
    # Create a simple threading lock
    lock = create_lock("threading", name="example_lock_1")
    
    async def worker(worker_id: int):
        logger.info(f"Worker {worker_id} trying to acquire lock...")
        
        async with lock:
            logger.info(f"Worker {worker_id} acquired lock, doing work...")
            await asyncio.sleep(1)  # Simulate work
            logger.info(f"Worker {worker_id} finished work")
        
        logger.info(f"Worker {worker_id} released lock")
    
    # Run multiple workers concurrently
    tasks = [worker(i) for i in range(3)]
    await asyncio.gather(*tasks)


async def example_lock_context_manager():
    """
    Example 2: Using lock_context for timeout handling
    """
    print("\n=== Example 2: Lock Context with Timeout ===")
    
    lock = ThreadingLock(name="timeout_example")
    
    async def long_running_task():
        async with lock:
            logger.info("Long running task started")
            await asyncio.sleep(2)
            logger.info("Long running task completed")
    
    async def quick_task():
        try:
            async with lock_context(lock, timeout=0.5):
                logger.info("Quick task acquired lock")
                await asyncio.sleep(0.1)
        except TimeoutError:
            logger.warning("Quick task timed out waiting for lock")
    
    # Start long task first, then try quick task
    await asyncio.gather(
        long_running_task(),
        asyncio.sleep(0.1),  # Small delay
        quick_task(),
        return_exceptions=True
    )


async def example_lock_manager_usage():
    """
    Example 3: Using LockManager for organized lock management
    """
    print("\n=== Example 3: Lock Manager Usage ===")
    
    # Create a custom lock manager
    manager = LockManager()
    
    # Create different locks for different purposes
    db_lock = manager.get_or_create_lock("database_operations", "threading", name="db_lock")
    file_lock = manager.get_or_create_lock("file_operations", "threading", name="file_lock")
    cache_lock = manager.get_or_create_lock("cache_operations", "threading", name="cache_lock")
    
    async def database_operation(operation_id: int):
        async with db_lock:
            logger.info(f"DB Operation {operation_id}: Executing database query")
            await asyncio.sleep(0.5)
    
    async def file_operation(operation_id: int):
        async with file_lock:
            logger.info(f"File Operation {operation_id}: Reading/Writing file")
            await asyncio.sleep(0.3)
    
    async def cache_operation(operation_id: int):
        async with cache_lock:
            logger.info(f"Cache Operation {operation_id}: Updating cache")
            await asyncio.sleep(0.2)
    
    # Run mixed operations concurrently
    tasks = []
    for i in range(2):
        tasks.extend([
            database_operation(i),
            file_operation(i),
            cache_operation(i)
        ])
    
    await asyncio.gather(*tasks)
    
    # Show lock manager status
    logger.info(f"Managed locks: {manager.list_locks()}")


async def example_global_lock_manager():
    """
    Example 4: Using the default global lock manager
    """
    print("\n=== Example 4: Global Lock Manager ===")
    
    # Get the default global manager
    global_manager = get_default_lock_manager()
    
    # Create locks through global manager
    lock1 = global_manager.get_or_create_lock("global_resource_1", "threading")
    lock2 = global_manager.get_or_create_lock("global_resource_2", "threading")
    
    # Subsequent calls return the same lock instances
    same_lock1 = global_manager.get_or_create_lock("global_resource_1", "threading")
    assert lock1 is same_lock1, "Should return the same lock instance"
    
    async def access_global_resource(resource_name: str, worker_id: int):
        lock = global_manager.get_or_create_lock(resource_name, "threading")
        async with lock:
            logger.info(f"Worker {worker_id} accessing {resource_name}")
            await asyncio.sleep(0.3)
    
    # Multiple workers accessing different global resources
    tasks = [
        access_global_resource("global_resource_1", 1),
        access_global_resource("global_resource_2", 2),
        access_global_resource("global_resource_1", 3),  # Will wait for worker 1
        access_global_resource("global_resource_2", 4),  # Will wait for worker 2
    ]
    
    await asyncio.gather(*tasks)
    
    logger.info(f"Global manager locks: {global_manager.list_locks()}")


async def example_error_handling():
    """
    Example 5: Error handling and edge cases
    """
    print("\n=== Example 5: Error Handling ===")
    
    lock = ThreadingLock(name="error_example")
    
    async def task_with_exception():
        try:
            async with lock:
                logger.info("Task started, will raise exception")
                await asyncio.sleep(0.1)
                raise ValueError("Simulated error")
        except ValueError as e:
            logger.info(f"Caught exception: {e}")
            # Lock should be automatically released even if exception occurs
        
        # Verify lock is released
        logger.info(f"Lock is locked: {lock.is_locked()}")
    
    async def normal_task():
        # Wait a bit to ensure the first task starts
        await asyncio.sleep(0.05)
        
        async with lock:
            logger.info("Normal task acquired lock successfully")
            await asyncio.sleep(0.1)
    
    # Run both tasks
    await asyncio.gather(
        task_with_exception(),
        normal_task(),
        return_exceptions=True
    )


async def example_lightrag_integration():
    """
    Example 6: LightRAG-style integration pattern
    """
    print("\n=== Example 6: LightRAG Integration Pattern ===")
    
    # Simulate multiple collections (workspaces)
    collections = ["collection_1", "collection_2", "collection_3"]
    
    # Create workspace-specific locks
    workspace_locks = {}
    for collection in collections:
        lock_name = f"lightrag_graph_lock_{collection}"
        workspace_locks[collection] = create_lock("threading", name=lock_name)
    
    async def process_documents(collection: str, doc_batch: List[str]):
        """Simulate document processing with collection-specific locking"""
        lock = workspace_locks[collection]
        
        async with lock:
            logger.info(f"Processing {len(doc_batch)} documents for {collection}")
            
            # Simulate chunking
            await asyncio.sleep(0.2)
            logger.info(f"  {collection}: Chunking completed")
            
            # Simulate graph indexing
            await asyncio.sleep(0.3)
            logger.info(f"  {collection}: Graph indexing completed")
            
            logger.info(f"  {collection}: Document processing finished")
    
    # Simulate concurrent document processing across different collections
    tasks = []
    for i, collection in enumerate(collections):
        doc_batch = [f"doc_{j}" for j in range(3)]
        tasks.append(process_documents(collection, doc_batch))
        
        # Also add a second batch for some collections to show queueing
        if i < 2:
            doc_batch_2 = [f"doc_batch2_{j}" for j in range(2)]
            tasks.append(process_documents(collection, doc_batch_2))
    
    # Process all tasks concurrently
    # Collections will process in parallel, but batches within same collection will be serialized
    await asyncio.gather(*tasks)


async def run_all_examples():
    """Run all examples sequentially"""
    print("Starting Concurrent Control Examples...")
    
    await example_basic_threading_lock()
    await example_lock_context_manager()
    await example_lock_manager_usage()
    await example_global_lock_manager()
    await example_error_handling()
    await example_lightrag_integration()
    
    print("\n=== All Examples Completed ===")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples()) 