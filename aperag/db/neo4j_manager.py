import os
import re
import asyncio
import logging
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j import exceptions as neo4jExceptions
from typing import Optional

logger = logging.getLogger(__name__)


class Neo4jDriverManager:
    """Global Neo4j Driver Manager with lazy lock initialization to avoid event loop conflicts."""
    
    _driver: Optional[AsyncDriver] = None
    _lock: Optional[asyncio.Lock] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Lazy load lock to ensure it's created in the correct event loop."""
        if cls._lock is None:
            # The asyncio.Lock() will be created in the currently running event loop
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    async def get_driver(cls) -> AsyncDriver:
        """Get global shared Neo4j Driver instance, initialize if not exists."""
        if cls._driver is None:
            lock = cls._get_lock()
            async with lock:
                # Double-check locking
                if cls._driver is None:
                    uri = os.environ.get("NEO4J_URI")
                    username = os.environ.get("NEO4J_USERNAME")
                    password = os.environ.get("NEO4J_PASSWORD")
                    
                    if not uri or not username or not password:
                        raise ValueError("Neo4j environment variables not properly configured")
                    
                    # Parse additional configuration
                    max_connection_pool_size = int(
                        os.environ.get("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")
                    )
                    connection_timeout = float(
                        os.environ.get("NEO4J_CONNECTION_TIMEOUT", "30.0")
                    )
                    connection_acquisition_timeout = float(
                        os.environ.get("NEO4J_CONNECTION_ACQUISITION_TIMEOUT", "30.0")
                    )
                    max_transaction_retry_time = float(
                        os.environ.get("NEO4J_MAX_TRANSACTION_RETRY_TIME", "30.0")
                    )
                    
                    logger.info(f"Initializing global Neo4j driver: {uri}")
                    cls._driver = AsyncGraphDatabase.driver(
                        uri,
                        auth=(username, password),
                        max_connection_pool_size=max_connection_pool_size,
                        connection_timeout=connection_timeout,
                        connection_acquisition_timeout=connection_acquisition_timeout,
                        max_transaction_retry_time=max_transaction_retry_time,
                    )
                    
                    # Verify connectivity
                    await cls._driver.verify_connectivity()
                    logger.info("Global Neo4j driver initialized successfully")
                    
        return cls._driver

    @classmethod
    async def close_driver(cls):
        """Close global Neo4j Driver instance."""
        if cls._driver:
            lock = cls._get_lock()
            async with lock:
                if cls._driver:
                    logger.info("Closing global Neo4j driver")
                    await cls._driver.close()
                    cls._driver = None
                    # Reset lock after closing to allow recreation in new event loop
                    cls._lock = None
                    logger.info("Global Neo4j driver closed")

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the global driver is initialized."""
        return cls._driver is not None

    @classmethod
    async def prepare_neo4j_database(cls, workspace: str) -> str:
        """
        Prepare Neo4j database (create database and indexes if needed).
        Uses Neo4j's IF NOT EXISTS for idempotent operations.
        """
        DATABASE = os.environ.get(
            "NEO4J_DATABASE", re.sub(r"[^a-zA-Z0-9-]", "-", workspace)
        )
        
        logger.debug(f"Preparing Neo4j database: {DATABASE}")
        driver = await cls.get_driver()
        
        # Try to connect to the target database first
        try:
            async with driver.session(database=DATABASE) as session:
                # Test connection to target database
                result = await session.run("MATCH (n) RETURN n LIMIT 0")
                await result.consume()
                logger.debug(f"Connected to existing database: {DATABASE}")
                
                # Create indexes (idempotent operation)
                await cls._create_indexes(driver, DATABASE)
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
                    await cls._create_indexes(driver, DATABASE)
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
                        return await cls._prepare_default_database(driver)
                    else:
                        logger.error(f"Failed to create database {DATABASE}: {e}")
                        raise e
            else:
                logger.error(f"Unexpected client error for database {DATABASE}: {e}")
                raise e

    @classmethod
    async def _prepare_default_database(cls, driver: AsyncDriver) -> str:
        """Prepare the default database when custom database creation is not supported."""
        # Connect to default database (None means default)
        try:
            async with driver.session() as session:
                result = await session.run("MATCH (n) RETURN n LIMIT 0")
                await result.consume()
                logger.info("Connected to default database")
                
            # Create indexes on default database
            await cls._create_indexes(driver, None)
            return "neo4j"  # Default database name
            
        except Exception as e:
            logger.error(f"Failed to connect to default database: {e}")
            raise RuntimeError("Failed to connect to any database") from e

    @classmethod
    async def _create_indexes(cls, driver: AsyncDriver, database: Optional[str]):
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


# Singleton instance
neo4j_manager = Neo4jDriverManager() 