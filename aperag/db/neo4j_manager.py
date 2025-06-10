import os
import re
import asyncio
import logging
import weakref
from typing import Optional, Dict, Any, Set
from contextlib import asynccontextmanager
from collections import defaultdict
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j import exceptions as neo4jExceptions

logger = logging.getLogger(__name__)


class Neo4jConnectionConfig:
    """Neo4j connection configuration"""
    
    def __init__(
        self,
        uri: str = None,
        username: str = None, 
        password: str = None,
        max_connection_pool_size: int = 50,
        connection_timeout: float = 30.0,
        connection_acquisition_timeout: float = 30.0,
        max_transaction_retry_time: float = 30.0,
        # Pool specific settings
        pool_max_size: int = 10,  # Maximum connections per event loop
        pool_min_size: int = 2,   # Minimum connections to maintain
    ):
        self.uri = uri or os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
        self.username = username or os.environ.get("NEO4J_USERNAME", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "neo4j")
        self.max_connection_pool_size = max_connection_pool_size
        self.connection_timeout = connection_timeout
        self.connection_acquisition_timeout = connection_acquisition_timeout
        self.max_transaction_retry_time = max_transaction_retry_time
        self.pool_max_size = pool_max_size
        self.pool_min_size = pool_min_size

    def to_driver_config(self) -> Dict[str, Any]:
        """Convert to driver configuration dictionary"""
        return {
            "max_connection_pool_size": self.max_connection_pool_size,
            "connection_timeout": self.connection_timeout,
            "connection_acquisition_timeout": self.connection_acquisition_timeout,
            "max_transaction_retry_time": self.max_transaction_retry_time,
        }


class PooledConnectionManager:
    """
    Pooled connection manager that can be borrowed and returned.
    Each instance is tied to a specific event loop.
    """
    
    def __init__(self, config: Neo4jConnectionConfig, pool: 'EventLoopConnectionPool'):
        self.config = config
        self.pool = pool
        self._driver: Optional[AsyncDriver] = None
        self._is_initialized = False
        self._in_use = False
        self._databases: Set[str] = set()

    async def get_driver(self) -> AsyncDriver:
        """Get the Neo4j driver instance."""
        if not self._is_initialized:
            await self._initialize_driver()
        return self._driver

    async def _initialize_driver(self):
        """Initialize the Neo4j driver"""
        if self._driver is not None:
            return
            
        logger.debug(f"Initializing pooled Neo4j driver: {self.config.uri}")
        
        self._driver = AsyncGraphDatabase.driver(
            self.config.uri,
            auth=(self.config.username, self.config.password),
            **self.config.to_driver_config()
        )
        
        # Verify connectivity
        await self._driver.verify_connectivity()
        self._is_initialized = True
        logger.debug("Pooled Neo4j driver initialized successfully")

    async def prepare_database(self, workspace: str) -> str:
        """Prepare database and cache the result."""
        database_name = await self._prepare_database_impl(workspace)
        self._databases.add(database_name)
        return database_name

    async def _prepare_database_impl(self, workspace: str) -> str:
        """Implementation of database preparation."""
        DATABASE = os.environ.get(
            "NEO4J_DATABASE", re.sub(r"[^a-zA-Z0-9-]", "-", workspace)
        )
        
        logger.debug(f"Preparing Neo4j database: {DATABASE}")
        driver = await self.get_driver()
        
        # Try to connect to the target database first
        try:
            async with driver.session(database=DATABASE) as session:
                result = await session.run("MATCH (n) RETURN n LIMIT 0")
                await result.consume()
                logger.debug(f"Connected to existing database: {DATABASE}")
                
                # Create indexes (idempotent operation)
                await self._create_indexes(driver, DATABASE)
                return DATABASE
                
        except neo4jExceptions.AuthError as e:
            logger.error(f"Authentication failed for {DATABASE}")
            raise e
        except neo4jExceptions.ServiceUnavailable as e:
            logger.error(f"Database {DATABASE} is not available")
            raise e
        except neo4jExceptions.ClientError as e:
            if e.code == "Neo.ClientError.Database.DatabaseNotFound":
                logger.info(f"Database {DATABASE} not found, attempting to create")
                try:
                    async with driver.session() as session:
                        result = await session.run(f"CREATE DATABASE `{DATABASE}` IF NOT EXISTS")
                        await result.consume()
                        logger.info(f"Database {DATABASE} created successfully")
                        
                    await self._create_indexes(driver, DATABASE)
                    return DATABASE
                    
                except (neo4jExceptions.ClientError, neo4jExceptions.DatabaseError) as e:
                    if (e.code == "Neo.ClientError.Statement.UnsupportedAdministrationCommand") or \
                       (e.code == "Neo.DatabaseError.Statement.ExecutionFailed"):
                        logger.warning(
                            f"This Neo4j instance does not support creating databases. "
                            f"Using default database instead."
                        )
                        return await self._prepare_default_database(driver)
                    else:
                        logger.error(f"Failed to create database {DATABASE}: {e}")
                        raise e
            else:
                logger.error(f"Unexpected client error for database {DATABASE}: {e}")
                raise e

    async def _prepare_default_database(self, driver: AsyncDriver) -> str:
        """Prepare the default database."""
        try:
            async with driver.session() as session:
                result = await session.run("MATCH (n) RETURN n LIMIT 0")
                await result.consume()
                logger.info("Connected to default database")
                
            await self._create_indexes(driver, None)
            return "neo4j"
            
        except Exception as e:
            logger.error(f"Failed to connect to default database: {e}")
            raise RuntimeError("Failed to connect to any database") from e

    async def _create_indexes(self, driver: AsyncDriver, database: Optional[str]):
        """Create necessary indexes."""
        async with driver.session(database=database) as session:
            try:
                result = await session.run(
                    "CREATE INDEX IF NOT EXISTS FOR (n:base) ON (n.entity_id)"
                )
                await result.consume()
                logger.debug(f"Ensured index exists for base nodes on entity_id in database: {database or 'default'}")
            except Exception as e:
                logger.warning(f"Could not create index in database {database or 'default'}: {e}")

    async def close(self):
        """Close the driver and clean up resources"""
        if self._driver:
            logger.debug("Closing pooled Neo4j driver")
            await self._driver.close()
            self._driver = None
            self._is_initialized = False
            self._databases.clear()

    def mark_in_use(self):
        """Mark this connection as in use."""
        self._in_use = True

    def mark_available(self):
        """Mark this connection as available."""
        self._in_use = False

    @property
    def is_in_use(self) -> bool:
        """Check if this connection is currently in use."""
        return self._in_use


class EventLoopConnectionPool:
    """
    Connection pool for a specific event loop.
    Manages borrowing and returning of connections.
    """
    
    def __init__(self, config: Neo4jConnectionConfig, loop_id: str):
        self.config = config
        self.loop_id = loop_id
        self._available_connections: list[PooledConnectionManager] = []
        self._in_use_connections: Set[PooledConnectionManager] = set()
        self._lock = asyncio.Lock()
        self._total_connections = 0

    async def borrow_connection(self) -> PooledConnectionManager:
        """Borrow a connection from the pool."""
        async with self._lock:
            # Try to get an available connection
            if self._available_connections:
                connection = self._available_connections.pop()
                connection.mark_in_use()
                self._in_use_connections.add(connection)
                logger.debug(f"Borrowed existing connection from pool (loop: {self.loop_id})")
                return connection
            
            # Create new connection if under limit
            if self._total_connections < self.config.pool_max_size:
                connection = PooledConnectionManager(self.config, self)
                await connection._initialize_driver()
                connection.mark_in_use()
                self._in_use_connections.add(connection)
                self._total_connections += 1
                logger.debug(f"Created new pooled connection (loop: {self.loop_id}, total: {self._total_connections})")
                return connection
            
            # Pool is full, wait for a connection to be returned
            # For now, create a temporary connection (could be improved with waiting logic)
            logger.warning(f"Connection pool full (loop: {self.loop_id}), creating temporary connection")
            connection = PooledConnectionManager(self.config, self)
            await connection._initialize_driver()
            connection.mark_in_use()
            return connection

    async def return_connection(self, connection: PooledConnectionManager):
        """Return a connection to the pool."""
        async with self._lock:
            if connection in self._in_use_connections:
                self._in_use_connections.remove(connection)
                connection.mark_available()
                
                # Only keep connections if under max and they're healthy
                if len(self._available_connections) < self.config.pool_max_size:
                    self._available_connections.append(connection)
                    logger.debug(f"Returned connection to pool (loop: {self.loop_id})")
                else:
                    # Pool is full, close the connection
                    await connection.close()
                    self._total_connections -= 1
                    logger.debug(f"Closed excess connection (loop: {self.loop_id}, total: {self._total_connections})")
            else:
                # This was a temporary connection, just close it
                await connection.close()
                logger.debug(f"Closed temporary connection (loop: {self.loop_id})")

    async def close_all(self):
        """Close all connections in this pool."""
        async with self._lock:
            # Close available connections
            for connection in self._available_connections:
                await connection.close()
            self._available_connections.clear()
            
            # Close in-use connections
            for connection in self._in_use_connections:
                await connection.close()
            self._in_use_connections.clear()
            
            self._total_connections = 0
            logger.info(f"Closed all connections in pool (loop: {self.loop_id})")

    @property
    def stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        return {
            "available": len(self._available_connections),
            "in_use": len(self._in_use_connections),
            "total": self._total_connections,
            "max_size": self.config.pool_max_size
        }


class GlobalNeo4jConnectionPool:
    """
    Global connection pool manager for Neo4j connections.
    Maintains separate pools for each event loop to avoid conflicts.
    """
    
    _instance: Optional['GlobalNeo4jConnectionPool'] = None
    _config: Optional[Neo4jConnectionConfig] = None
    
    def __init__(self):
        self._pools: Dict[str, EventLoopConnectionPool] = {}
        self._loop_refs: Dict[str, weakref.ReferenceType] = {}
        self._lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_config(cls, config: Neo4jConnectionConfig):
        """Set the global configuration."""
        cls._config = config
    
    @classmethod
    def get_config(cls) -> Neo4jConnectionConfig:
        """Get the global configuration."""
        if cls._config is None:
            cls._config = Neo4jConnectionConfig()
        return cls._config
    
    def _get_loop_id(self) -> str:
        """Get a unique identifier for the current event loop."""
        try:
            loop = asyncio.get_running_loop()
            return f"{id(loop)}"
        except RuntimeError:
            raise RuntimeError("No running event loop found")
    
    async def get_pool(self) -> EventLoopConnectionPool:
        """Get or create a connection pool for the current event loop."""
        loop_id = self._get_loop_id()
        
        # Check if we have a pool for this event loop
        if loop_id in self._pools:
            return self._pools[loop_id]
        
        # Create new pool for this event loop
        async with self._lock:
            # Double check after acquiring lock
            if loop_id in self._pools:
                return self._pools[loop_id]
            
            # Create new pool
            config = self.get_config()
            pool = EventLoopConnectionPool(config, loop_id)
            self._pools[loop_id] = pool
            
            # Store weak reference to detect when event loop is garbage collected
            loop = asyncio.get_running_loop()
            self._loop_refs[loop_id] = weakref.ref(loop, lambda ref: self._cleanup_pool(loop_id))
            
            logger.info(f"Created new connection pool for event loop {loop_id}")
            return pool
    
    def _cleanup_pool(self, loop_id: str):
        """Cleanup pool when event loop is garbage collected."""
        if loop_id in self._pools:
            # Note: We can't use async here since we're in a finalizer
            # The pool will be cleaned up when the worker shuts down
            del self._pools[loop_id]
            if loop_id in self._loop_refs:
                del self._loop_refs[loop_id]
            logger.info(f"Cleaned up connection pool for event loop {loop_id}")
    
    async def borrow_connection(self) -> PooledConnectionManager:
        """Borrow a connection from the appropriate pool."""
        pool = await self.get_pool()
        return await pool.borrow_connection()
    
    async def return_connection(self, connection: PooledConnectionManager):
        """Return a connection to the appropriate pool."""
        await connection.pool.return_connection(connection)
    
    async def close_all_pools(self):
        """Close all connection pools."""
        async with self._lock:
            for pool in self._pools.values():
                await pool.close_all()
            self._pools.clear()
            self._loop_refs.clear()
            logger.info("Closed all connection pools")
    
    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for all pools."""
        return {loop_id: pool.stats for loop_id, pool in self._pools.items()}


# Context manager for borrowing connections
class BorrowedConnection:
    """
    Context manager for safely borrowing and returning connections.
    """
    
    def __init__(self, pool_manager: GlobalNeo4jConnectionPool):
        self.pool_manager = pool_manager
        self.connection: Optional[PooledConnectionManager] = None
        self._database_cache: Dict[str, str] = {}
    
    async def __aenter__(self) -> 'BorrowedConnection':
        self.connection = await self.pool_manager.borrow_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            await self.pool_manager.return_connection(self.connection)
            self.connection = None
    
    async def get_driver(self) -> AsyncDriver:
        """Get the driver from the borrowed connection."""
        if not self.connection:
            raise RuntimeError("No connection borrowed")
        return await self.connection.get_driver()
    
    async def prepare_database(self, workspace: str) -> str:
        """Prepare database using the borrowed connection."""
        if not self.connection:
            raise RuntimeError("No connection borrowed")
        
        # Use cache to avoid repeated database preparation
        if workspace in self._database_cache:
            return self._database_cache[workspace]
        
        database_name = await self.connection.prepare_database(workspace)
        self._database_cache[workspace] = database_name
        return database_name


# Factory for accessing the global pool
class Neo4jConnectionFactory:
    """
    Event-loop-safe connection factory with global connection pooling.
    """
    
    @classmethod
    def get_global_pool(cls) -> GlobalNeo4jConnectionPool:
        """Get the global connection pool instance."""
        return GlobalNeo4jConnectionPool()
    
    @classmethod
    def borrow_connection(cls) -> BorrowedConnection:
        """Borrow a connection from the global pool."""
        pool = cls.get_global_pool()
        return BorrowedConnection(pool)
    
    @classmethod
    async def get_pool_stats(cls) -> Dict[str, Dict[str, int]]:
        """Get statistics for all connection pools."""
        pool = cls.get_global_pool()
        return pool.get_all_stats()


# Celery/Prefect Worker Signal Handlers
def setup_worker_neo4j_config(**kwargs):
    """Signal handler to setup Neo4j configuration when a worker process starts."""
    # Initialize global configuration
    config = Neo4jConnectionConfig()
    GlobalNeo4jConnectionPool.set_config(config)
    logger.info(f"Worker process {os.getpid()}: Neo4j global pool configuration initialized")


async def cleanup_worker_neo4j_config_async(**kwargs):
    """Async cleanup of all connection pools."""
    pool = GlobalNeo4jConnectionPool()
    await pool.close_all_pools()
    logger.info(f"Worker process {os.getpid()}: All Neo4j connection pools closed")


def cleanup_worker_neo4j_config(**kwargs):
    """Signal handler to cleanup Neo4j configuration when a worker process shuts down."""
    try:
        # Try to run cleanup in existing event loop
        loop = asyncio.get_running_loop()
        loop.create_task(cleanup_worker_neo4j_config_async(**kwargs))
    except RuntimeError:
        # No running loop, run in new one
        asyncio.run(cleanup_worker_neo4j_config_async(**kwargs)) 