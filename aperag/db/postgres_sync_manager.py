import os
import logging
import threading
from typing import Optional, Dict, Any
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
import psycopg2.extensions

logger = logging.getLogger(__name__)


class PostgreSQLSyncConnectionManager:
    """
    Worker-level PostgreSQL connection manager using sync driver.
    This avoids event loop issues and provides true connection reuse across Celery tasks.
    """
    
    # Class-level storage for worker-scoped connection pool
    _pool: Optional[ThreadedConnectionPool] = None
    _lock = threading.Lock()
    _config: Optional[Dict[str, Any]] = None
    _workspace: Optional[str] = None
    
    @classmethod
    def initialize(cls, config: Optional[Dict[str, Any]] = None):
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
                        "workspace": os.environ.get("POSTGRES_WORKSPACE", "default"),
                        "min_connections": int(os.environ.get("POSTGRES_MIN_CONNECTIONS", "5")),
                        "max_connections": int(os.environ.get("POSTGRES_MAX_CONNECTIONS", "20")),
                    }
                
                cls._workspace = cls._config["workspace"]
                
                logger.info(f"Initializing PostgreSQL sync connection pool for worker {os.getpid()}")
                
                # Create connection string
                dsn = f"host={cls._config['host']} port={cls._config['port']} " \
                      f"dbname={cls._config['database']} user={cls._config['user']} " \
                      f"password={cls._config['password']}"
                
                # Create threaded connection pool
                cls._pool = ThreadedConnectionPool(
                    cls._config["min_connections"],
                    cls._config["max_connections"],
                    dsn
                )
                
                # Verify connectivity
                conn = cls._pool.getconn()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                    logger.info(f"PostgreSQL sync connection pool initialized successfully for worker {os.getpid()}")
                except Exception as e:
                    logger.error(f"Failed to verify PostgreSQL connectivity: {e}")
                    raise
                finally:
                    cls._pool.putconn(conn)
                
                # Initialize tables
                cls._initialize_tables()
    
    @classmethod
    def _initialize_tables(cls):
        """Initialize required tables if they don't exist."""
        from aperag.graph.lightrag.kg.postgres_impl import TABLES
        
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables
            for table_name, table_info in TABLES.items():
                try:
                    # Check if table exists
                    cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                except psycopg2.ProgrammingError:
                    # Table doesn't exist, create it
                    conn.rollback()  # Reset transaction state
                    try:
                        logger.info(f"PostgreSQL, Creating table {table_name}")
                        cursor.execute(table_info["ddl"])
                        conn.commit()
                        logger.info(f"PostgreSQL, Successfully created table {table_name}")
                    except Exception as e:
                        logger.error(f"PostgreSQL, Failed to create table {table_name}: {e}")
                        conn.rollback()
                        raise
                else:
                    # Table exists
                    conn.rollback()
                
                # Create index for id column
                try:
                    index_name = f"idx_{table_name.lower()}_id"
                    cursor.execute(f"""
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = '{index_name}'
                        AND tablename = '{table_name.lower()}'
                    """)
                    
                    if not cursor.fetchone():
                        cursor.execute(f"CREATE INDEX {index_name} ON {table_name}(id)")
                        conn.commit()
                        logger.info(f"PostgreSQL, Created index {index_name}")
                    else:
                        conn.rollback()
                except Exception as e:
                    logger.error(f"PostgreSQL, Failed to create index on table {table_name}: {e}")
                    conn.rollback()
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a connection from the pool."""
        if cls._pool is None:
            cls.initialize()
        
        conn = cls._pool.getconn()
        try:
            # Set autocommit mode
            conn.autocommit = True
            yield conn
        except Exception as e:
            # Rollback on error
            if not conn.closed:
                conn.rollback()
            raise
        finally:
            # Return connection to pool
            if not conn.closed:
                cls._pool.putconn(conn)
    
    @classmethod
    @contextmanager
    def get_cursor(cls, dictionary=True):
        """Get a cursor from a pooled connection."""
        with cls.get_connection() as conn:
            if dictionary:
                cursor = conn.cursor(cursor_factory=DictCursor)
            else:
                cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
    
    @classmethod
    def get_workspace(cls) -> str:
        """Get the current workspace."""
        if cls._workspace is None:
            cls.initialize()
        return cls._workspace
    
    @classmethod
    def execute_query(cls, sql: str, params: tuple = None, fetch_one: bool = False, 
                     fetch_all: bool = False) -> Any:
        """Execute a query and return results."""
        with cls.get_cursor() as cursor:
            cursor.execute(sql, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount
    
    @classmethod
    def execute_many(cls, sql: str, params_list: list):
        """Execute multiple statements."""
        with cls.get_cursor() as cursor:
            cursor.executemany(sql, params_list)
            return cursor.rowcount
    
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