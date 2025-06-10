import os
import logging
import threading
from typing import Optional, Dict, Any, Tuple, List, Union
from contextlib import contextmanager
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class PostgreSQLSyncConnectionManager:
    """
    Worker-level PostgreSQL connection manager using sync driver with connection pooling.
    This avoids event loop issues and provides true connection reuse across Celery tasks.
    """
    
    # Class-level storage for worker-scoped connection pool
    _pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
    _lock = threading.Lock()
    _config: Optional[Dict[str, Any]] = None
    _workspace: Optional[str] = None
    
    @classmethod
    def initialize(cls, config: Optional[Dict[str, Any]] = None, workspace: str = "default"):
        """Initialize the connection manager with configuration."""
        with cls._lock:
            if cls._pool is None:
                # Use provided config or environment variables
                if config:
                    cls._config = config
                else:
                    cls._config = {
                        "host": os.environ.get("POSTGRES_HOST", "localhost"),
                        "port": int(os.environ.get("POSTGRES_PORT", 5432)),
                        "user": os.environ.get("POSTGRES_USER", "postgres"),
                        "password": os.environ.get("POSTGRES_PASSWORD", "password"),
                        "database": os.environ.get("POSTGRES_DATABASE", "postgres"),
                        "minconn": int(os.environ.get("POSTGRES_MIN_CONNECTIONS", 2)),
                        "maxconn": int(os.environ.get("POSTGRES_MAX_CONNECTIONS", 20)),
                    }
                
                cls._workspace = workspace
                
                if not all([cls._config["user"], cls._config["password"], cls._config["database"]]):
                    raise ValueError("Missing required PostgreSQL configuration: user, password, or database")
                
                logger.info(f"Initializing PostgreSQL sync connection pool for worker {os.getpid()}")
                
                try:
                    cls._pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=cls._config["minconn"],
                        maxconn=cls._config["maxconn"],
                        host=cls._config["host"],
                        port=cls._config["port"],
                        user=cls._config["user"],
                        password=cls._config["password"],
                        database=cls._config["database"],
                        cursor_factory=RealDictCursor
                    )
                    
                    # Test connectivity
                    with cls.get_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT 1")
                            cursor.fetchone()
                    
                    logger.info(f"PostgreSQL sync connection pool initialized successfully for worker {os.getpid()}")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
                    raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a connection from the pool."""
        if cls._pool is None:
            cls.initialize()
        
        conn = None
        try:
            conn = cls._pool.getconn()
            yield conn
        finally:
            if conn:
                cls._pool.putconn(conn)
    
    @classmethod
    def get_workspace(cls) -> str:
        """Get the current workspace."""
        return cls._workspace or "default"
    
    @classmethod
    def execute_query(
        cls, 
        query: str, 
        params: Optional[Tuple] = None, 
        fetch_one: bool = False, 
        fetch_all: bool = False
    ) -> Union[None, Dict, List[Dict]]:
        """Execute a query and return results."""
        with cls.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    if fetch_one:
                        result = cursor.fetchone()
                        return dict(result) if result else None
                    elif fetch_all:
                        results = cursor.fetchall()
                        return [dict(row) for row in results] if results else []
                    else:
                        # For INSERT/UPDATE/DELETE operations
                        conn.commit()
                        return None
                        
                except Exception as e:
                    conn.rollback()
                    logger.error(f"PostgreSQL query error: {e}")
                    logger.error(f"Query: {query}")
                    logger.error(f"Params: {params}")
                    raise
    
    @classmethod
    def close(cls):
        """Close the connection pool and clean up resources."""
        with cls._lock:
            if cls._pool:
                logger.info(f"Closing PostgreSQL connection pool for worker {os.getpid()}")
                cls._pool.closeall()
                cls._pool = None
                cls._config = None
                cls._workspace = None


# Celery signal handlers for worker lifecycle
def setup_worker_postgres(**kwargs):
    """Initialize PostgreSQL when worker starts."""
    PostgreSQLSyncConnectionManager.initialize()
    logger.info(f"Worker {os.getpid()}: PostgreSQL sync connection pool initialized")


def cleanup_worker_postgres(**kwargs):
    """Cleanup PostgreSQL when worker shuts down."""
    PostgreSQLSyncConnectionManager.close()
    logger.info(f"Worker {os.getpid()}: PostgreSQL sync connection pool closed") 