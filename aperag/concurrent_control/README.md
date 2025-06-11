# Universal Concurrent Control Module

A flexible and reusable concurrent control system that provides unified locking mechanisms for any Python application. This module is designed to handle different deployment scenarios and task queue environments.

## Features

- **Parameter-based Configuration**: No environment variable dependencies, fully configurable through parameters
- **Multi-instance Support**: Each component can have dedicated locks with unique identifiers
- **Universal Applicability**: Not limited to any specific use case (LightRAG, database operations, etc.)
- **Easy Extensibility**: Clear protocol interface for implementing new lock types
- **Production Ready**: Organized management and comprehensive error handling

## Supported Lock Types

### ThreadingLock
- **Best for**: Single-process environments (Celery `--pool=solo`, `--pool=threads`, `--pool=gevent`)
- **Implementation**: `threading.Lock` wrapped with `asyncio.to_thread`
- **Features**: 
  - Works with both coroutine and thread concurrency
  - Non-blocking for event loop
  - Lower overhead than distributed locks
- **Limitations**: Does NOT work across multiple processes

### RedisLock (Future)
- **Best for**: Multi-process environments (Celery `--pool=prefork`, distributed deployment)
- **Implementation**: Redis-based distributed locking (TODO)
- **Features**: 
  - Works across processes, containers, and machines
  - Automatic lock expiration to prevent deadlocks
  - Retry mechanisms for lock acquisition
- **Trade-offs**: Network overhead, Redis dependency

## Quick Start

### Basic Usage

```python
from aperag.concurrent_control import create_lock

# Create a threading lock
lock = create_lock("threading", name="my_operation")

async def critical_operation():
    async with lock:
        # Your protected operations here
        await some_critical_work()
```

### Lock Manager

```python
from aperag.concurrent_control import LockManager

# Create a manager for organized lock management
manager = LockManager()

# Create different locks for different purposes
db_lock = manager.get_or_create_lock("database_ops", "threading")
file_lock = manager.get_or_create_lock("file_ops", "threading")

async def database_operation():
    async with db_lock:
        await execute_query()

async def file_operation():
    async with file_lock:
        await write_file()
```

### Global Lock Manager

```python
from aperag.concurrent_control import get_default_lock_manager

# Use the default global manager
global_manager = get_default_lock_manager()
lock = global_manager.get_or_create_lock("resource_name", "threading")
```

### Timeout Handling

```python
from aperag.concurrent_control import lock_context

async def operation_with_timeout():
    try:
        async with lock_context(my_lock, timeout=5.0):
            await some_operation()
    except TimeoutError:
        print("Operation timed out waiting for lock")
```

## Integration Examples

### LightRAG Integration

```python
from aperag.concurrent_control import create_lock

class LightRAGWorkspaceManager:
    def __init__(self, workspace: str):
        self.workspace = workspace
        # Create workspace-specific lock
        lock_name = f"lightrag_graph_lock_{workspace}"
        self.graph_lock = create_lock("threading", name=lock_name)
    
    async def process_documents(self, documents):
        async with self.graph_lock:
            await self._chunking_operation(documents)
            await self._graph_indexing_operation(documents)
```

### Database Operations

```python
from aperag.concurrent_control import LockManager

class DatabaseManager:
    def __init__(self):
        self.lock_manager = LockManager()
    
    async def migrate_schema(self, table_name: str):
        lock = self.lock_manager.get_or_create_lock(f"schema_{table_name}", "threading")
        async with lock:
            await self._perform_migration(table_name)
    
    async def batch_insert(self, table_name: str, data):
        lock = self.lock_manager.get_or_create_lock(f"insert_{table_name}", "threading")
        async with lock:
            await self._batch_insert_operation(table_name, data)
```

### File System Operations

```python
from aperag.concurrent_control import create_lock

# Global locks for file system operations
file_locks = {}

async def safe_file_operation(file_path: str):
    # Create lock per file path
    if file_path not in file_locks:
        file_locks[file_path] = create_lock("threading", name=f"file_{file_path}")
    
    lock = file_locks[file_path]
    async with lock:
        await modify_file(file_path)
```

## API Reference

### Core Functions

#### `create_lock(lock_type: str = "threading", **kwargs) -> LockProtocol`
Factory function to create appropriate lock implementation.

**Parameters:**
- `lock_type`: Type of lock ("threading" or "redis")
- `**kwargs`: Additional arguments for lock constructor

**Threading Lock Arguments:**
- `name`: Optional descriptive name for the lock

**Redis Lock Arguments (Future):**
- `key`: Redis key for the lock (required)
- `redis_url`: Redis connection URL
- `expire_time`: Lock expiration time in seconds
- `retry_times`: Number of retry attempts
- `retry_delay`: Delay between retries

#### `lock_context(lock: LockProtocol, timeout: float = None)`
Async context manager with timeout support.

### LockManager Class

#### `get_or_create_lock(lock_id: str, lock_type: str = "threading", **kwargs) -> LockProtocol`
Get existing lock or create new one with the given identifier.

#### `list_locks() -> Dict[str, str]`
List all managed locks with their types.

#### `remove_lock(lock_id: str) -> bool`
Remove a lock from the manager.

### Global Manager

#### `get_default_lock_manager() -> LockManager`
Get the default global lock manager instance.

## Deployment Recommendations

### Celery Deployment Modes

| Pool Type | Recommended Lock | Use Case |
|-----------|------------------|----------|
| `--pool=prefork` | `RedisLock` (Future) | Production multi-process |
| `--pool=threads` | `ThreadingLock` | Single-process multi-thread |
| `--pool=gevent` | `ThreadingLock` | Single-process async |
| `--pool=solo` | `ThreadingLock` | Development/testing |

### Configuration Examples

```python
# For development (single process)
lock = create_lock("threading", name="dev_lock")

# For production (multi-process) - Future
# lock = create_lock("redis", key="prod:my_app:lock", redis_url="redis://redis-cluster:6379")
```

## Error Handling

The module provides comprehensive error handling:

```python
from aperag.concurrent_control import create_lock, lock_context

lock = create_lock("threading")

# Automatic lock release on exceptions
async def operation_with_error():
    try:
        async with lock:
            await some_operation()
            raise ValueError("Something went wrong")
    except ValueError:
        # Lock is automatically released
        pass

# Timeout handling
async def operation_with_timeout():
    try:
        async with lock_context(lock, timeout=10.0):
            await long_operation()
    except TimeoutError:
        print("Operation timed out")
```

## Performance Considerations

### ThreadingLock
- **Pros**: Low overhead for single-process scenarios, no external dependencies
- **Cons**: Higher overhead than `asyncio.Lock`, process-local only

### RedisLock (Future)
- **Pros**: Works across processes and machines, built-in expiration
- **Cons**: Network overhead, Redis dependency, higher latency

## Migration Guide

### From asyncio.Lock

```python
# Before
import asyncio
lock = asyncio.Lock()

# After
from aperag.concurrent_control import create_lock
lock = create_lock("threading")
```

### From threading.Lock

```python
# Before
import threading
lock = threading.Lock()

def sync_operation():
    with lock:
        # sync code

# After
from aperag.concurrent_control import create_lock
lock = create_lock("threading")

async def async_operation():
    async with lock:
        # async code
```

## Testing

The module includes comprehensive unit tests. Run them with:

```bash
pytest tests/unit_test/concurrent_control/
```

## Future Enhancements

1. **RedisLock Implementation**: Complete Redis-based distributed locking
2. **Additional Lock Types**: Database-based locks, file-based locks
3. **Monitoring**: Lock usage metrics and performance monitoring
4. **Advanced Features**: Lock priorities, deadlock detection

## License

This module is part of the ApeRAG project and follows the same license terms. 