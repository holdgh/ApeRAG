import os
import re
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
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
        max_transaction_retry_time: float = 30.0
    ):
        self.uri = uri or os.environ.get("NEO4J_URI", "neo4j://localhost:7687")
        self.username = username or os.environ.get("NEO4J_USERNAME", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "neo4j")
        self.max_connection_pool_size = max_connection_pool_size
        self.connection_timeout = connection_timeout
        self.connection_acquisition_timeout = connection_acquisition_timeout
        self.max_transaction_retry_time = max_transaction_retry_time

    def to_driver_config(self) -> Dict[str, Any]:
        """Convert to driver configuration dictionary"""
        return {
            "max_connection_pool_size": self.max_connection_pool_size,
            "connection_timeout": self.connection_timeout,
            "connection_acquisition_timeout": self.connection_acquisition_timeout,
            "max_transaction_retry_time": self.max_transaction_retry_time,
        }


class Neo4jConnectionManager:
    """
    Neo4j connection manager using AsyncContextManager pattern.
    Each instance manages its own driver lifecycle.
    """
    
    def __init__(self, config: Neo4jConnectionConfig = None):
        self.config = config or Neo4jConnectionConfig()
        self._driver: Optional[AsyncDriver] = None
        self._is_initialized = False

    async def get_driver(self) -> AsyncDriver:
        """
        Get the Neo4j driver instance.
        Initializes driver if not already done.
        """
        if not self._is_initialized:
            await self._initialize_driver()
        return self._driver

    @asynccontextmanager
    async def driver_context(self):
        """
        Async context manager that provides a Neo4j driver instance.
        This is useful for temporary connections.
        """
        driver = await self.get_driver()
        try:
            yield driver
        finally:
            # Driver remains alive for the lifetime of this manager
            pass

    async def _initialize_driver(self):
        """Initialize the Neo4j driver"""
        if self._driver is not None:
            return
            
        logger.info(f"Initializing Neo4j driver: {self.config.uri}")
        
        self._driver = AsyncGraphDatabase.driver(
            self.config.uri,
            auth=(self.config.username, self.config.password),
            **self.config.to_driver_config()
        )
        
        # Verify connectivity
        await self._driver.verify_connectivity()
        self._is_initialized = True
        logger.info("Neo4j driver initialized successfully")

    async def close(self):
        """Close the driver and clean up resources"""
        if self._driver:
            logger.info("Closing Neo4j driver")
            await self._driver.close()
            self._driver = None
            self._is_initialized = False
            logger.info("Neo4j driver closed")

    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_driver()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    @staticmethod
    async def prepare_database(driver: AsyncDriver, workspace: str) -> str:
        """
        Prepare Neo4j database (create database and indexes if needed).
        Uses Neo4j's IF NOT EXISTS for idempotent operations.
        """
        DATABASE = os.environ.get(
            "NEO4J_DATABASE", re.sub(r"[^a-zA-Z0-9-]", "-", workspace)
        )
        
        logger.debug(f"Preparing Neo4j database: {DATABASE}")
        
        # Try to connect to the target database first
        try:
            async with driver.session(database=DATABASE) as session:
                # Test connection to target database
                result = await session.run("MATCH (n) RETURN n LIMIT 0")
                await result.consume()
                logger.debug(f"Connected to existing database: {DATABASE}")
                
                # Create indexes (idempotent operation)
                await Neo4jConnectionManager._create_indexes(driver, DATABASE)
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
                # Try to create the database
                try:
                    async with driver.session() as session:
                        result = await session.run(
                            f"CREATE DATABASE `{DATABASE}` IF NOT EXISTS"
                        )
                        await result.consume()
                        logger.info(f"Database {DATABASE} created successfully")
                        
                    # Create indexes after database creation
                    await Neo4jConnectionManager._create_indexes(driver, DATABASE)
                    return DATABASE
                    
                except (neo4jExceptions.ClientError, neo4jExceptions.DatabaseError) as e:
                    if (e.code == "Neo.ClientError.Statement.UnsupportedAdministrationCommand") or \
                       (e.code == "Neo.DatabaseError.Statement.ExecutionFailed"):
                        logger.warning(
                            f"This Neo4j instance does not support creating databases. "
                            f"Using default database instead. "
                            f"Consider using Neo4j Desktop/Enterprise version for multi-database support."
                        )
                        # Fall back to default database
                        return await Neo4jConnectionManager._prepare_default_database(driver)
                    else:
                        logger.error(f"Failed to create database {DATABASE}: {e}")
                        raise e
            else:
                logger.error(f"Unexpected client error for database {DATABASE}: {e}")
                raise e

    @staticmethod
    async def _prepare_default_database(driver: AsyncDriver) -> str:
        """Prepare the default database when custom database creation is not supported."""
        # Connect to default database (None means default)
        try:
            async with driver.session() as session:
                result = await session.run("MATCH (n) RETURN n LIMIT 0")
                await result.consume()
                logger.info("Connected to default database")
                
            # Create indexes on default database
            await Neo4jConnectionManager._create_indexes(driver, None)
            return "neo4j"  # Default database name
            
        except Exception as e:
            logger.error(f"Failed to connect to default database: {e}")
            raise RuntimeError("Failed to connect to any database") from e

    @staticmethod
    async def _create_indexes(driver: AsyncDriver, database: Optional[str]):
        """Create necessary indexes using IF NOT EXISTS (idempotent operation)."""
        async with driver.session(database=database) as session:
            try:
                # Use IF NOT EXISTS for idempotent index creation
                result = await session.run(
                    "CREATE INDEX IF NOT EXISTS FOR (n:base) ON (n.entity_id)"
                )
                await result.consume()
                logger.debug(f"Ensured index exists for base nodes on entity_id in database: {database or 'default'}")
                
            except Exception as e:
                # Log but don't fail on index creation issues
                logger.warning(f"Could not create index in database {database or 'default'}: {e}")


# Event-loop-safe connection factory for Celery/Prefect
class Neo4jConnectionFactory:
    """
    Event-loop-safe connection factory for Celery workers.
    Creates connections within the current event loop context.
    """
    
    _config: Optional[Neo4jConnectionConfig] = None
    
    @classmethod
    async def get_connection_manager(cls) -> Neo4jConnectionManager:
        """
        Create a new connection manager in the current event loop.
        This ensures no event loop conflicts.
        """
        # Get or create shared configuration
        if cls._config is None:
            # Use a simple threading lock for config initialization
            import threading
            if not hasattr(cls, '_thread_lock'):
                cls._thread_lock = threading.Lock()
            
            with cls._thread_lock:
                if cls._config is None:
                    cls._config = Neo4jConnectionConfig()
                    logger.info(f"Worker {os.getpid()}: Initialized shared Neo4j config")
        
        # Create new connection manager in current event loop
        manager = Neo4jConnectionManager(cls._config)
        logger.info(f"Worker {os.getpid()}: Created new Neo4j connection manager for current event loop")
        return manager
    
    @classmethod
    def reset_config(cls):
        """Reset configuration (useful for testing)"""
        cls._config = None


# Celery/Prefect Worker Signal Handlers
def setup_worker_neo4j_config(**kwargs):
    """Signal handler to setup Neo4j configuration when a worker process starts."""
    # Pre-initialize configuration to avoid repeated environment variable parsing
    config = Neo4jConnectionConfig()
    Neo4jConnectionFactory._config = config
    logger.info(f"Worker process {os.getpid()}: Neo4j configuration initialized")


def cleanup_worker_neo4j_config(**kwargs):
    """Signal handler to cleanup Neo4j configuration when a worker process shuts down."""
    Neo4jConnectionFactory.reset_config()
    logger.info(f"Worker process {os.getpid()}: Neo4j configuration cleaned up") 