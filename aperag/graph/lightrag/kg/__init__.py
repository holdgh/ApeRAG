# Import all storage implementations with conditional handling
try:
    from .neo4j_impl import Neo4JStorage
except ImportError:
    Neo4JStorage = None

try:
    from .neo4j_sync_impl import Neo4JSyncStorage
except ImportError:
    Neo4JSyncStorage = None

try:
    from .redis_impl import RedisKVStorage
except ImportError:
    RedisKVStorage = None

try:
    from .postgres_impl import PGKVStorage, PGVectorStorage, PGDocStatusStorage
except ImportError:
    PGKVStorage = None
    PGVectorStorage = None
    PGDocStatusStorage = None

try:
    from .postgres_sync_impl import PGOpsSyncDocStatusStorage, PGOpsSyncKVStorage, PGOpsSyncVectorStorage
except ImportError:
    PGOpsSyncDocStatusStorage = None
    PGOpsSyncKVStorage = None
    PGOpsSyncVectorStorage = None

try:
    from .qdrant_impl import QdrantVectorDBStorage
except ImportError:
    QdrantVectorDBStorage = None

STORAGE_IMPLEMENTATIONS = {
    "KV_STORAGE": {
        "implementations": [
            "RedisKVStorage",
            "PGKVStorage",
            "PGSyncKVStorage",
            "PGOpsSyncKVStorage",
        ],
        "required_methods": ["get_by_id", "upsert"],
    },
    "GRAPH_STORAGE": {
        "implementations": [
            "Neo4JStorage",
            "Neo4JSyncStorage",
            "Neo4JHybridStorage",
            "PGGraphStorage",
            "AGEStorage",
        ],
        "required_methods": ["upsert_node", "upsert_edge"],
    },
    "VECTOR_STORAGE": {
        "implementations": [
            "PGVectorStorage",
            "PGSyncVectorStorage",
            "PGOpsSyncVectorStorage",
            "QdrantVectorDBStorage",
        ],
        "required_methods": ["query", "upsert"],
    },
    "DOC_STATUS_STORAGE": {
        "implementations": [
            "PGDocStatusStorage",
            "PGSyncDocStatusStorage",
            "PGOpsSyncDocStatusStorage",
        ],
        "required_methods": ["get_docs_by_status"],
    },
}

# Storage implementation environment variable without default value
STORAGE_ENV_REQUIREMENTS: dict[str, list[str]] = {
    # KV Storage Implementations
    "RedisKVStorage": ["REDIS_URI"],
    "PGKVStorage": ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DATABASE"],
    "PGSyncKVStorage": ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DATABASE"],
    # Graph Storage Implementations
    "Neo4JStorage": ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"],
    "Neo4JSyncStorage": ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"],

    "PGGraphStorage": [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DATABASE",
    ],
    # Vector Storage Implementations
    "PGVectorStorage": ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DATABASE"],
    "PGSyncVectorStorage": ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DATABASE"],
    "QdrantVectorDBStorage": ["QDRANT_URL"],  # QDRANT_API_KEY has default value None
    # Document Status Storage Implementations
    "PGDocStatusStorage": ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DATABASE"],
    "PGSyncDocStatusStorage": ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DATABASE"],
}

# Storage implementation module mapping - build conditionally
STORAGES = {}

# Add Neo4J implementations
if Neo4JStorage is not None:
    STORAGES["Neo4JStorage"] = ".kg.neo4j_impl"

if Neo4JSyncStorage is not None:
    STORAGES["Neo4JSyncStorage"] = ".kg.neo4j_sync_impl"

# Add Redis implementations
if RedisKVStorage is not None:
    STORAGES["RedisKVStorage"] = ".kg.redis_impl"

# Add PostgreSQL async implementations
if PGKVStorage is not None:
    STORAGES["PGKVStorage"] = ".kg.postgres_impl"

if PGVectorStorage is not None:
    STORAGES["PGVectorStorage"] = ".kg.postgres_impl"

if PGDocStatusStorage is not None:
    STORAGES["PGDocStatusStorage"] = ".kg.postgres_impl"

if PGOpsSyncDocStatusStorage is not None:
    STORAGES["PGOpsSyncDocStatusStorage"] = ".kg.postgres_sync_impl"

if PGOpsSyncKVStorage is not None:
    STORAGES["PGOpsSyncKVStorage"] = ".kg.postgres_sync_impl"

if PGOpsSyncVectorStorage is not None:
    STORAGES["PGOpsSyncVectorStorage"] = ".kg.postgres_sync_impl"

# Add Qdrant implementations
if QdrantVectorDBStorage is not None:
    STORAGES["QdrantVectorDBStorage"] = ".kg.qdrant_impl"

def verify_storage_implementation(storage_type: str, storage_name: str) -> None:
    """Verify if storage implementation is compatible with specified storage type

    Args:
        storage_type: Storage type (KV_STORAGE, GRAPH_STORAGE etc.)
        storage_name: Storage implementation name

    Raises:
        ValueError: If storage implementation is incompatible or missing required methods
    """
    if storage_type not in STORAGE_IMPLEMENTATIONS:
        raise ValueError(f"Unknown storage type: {storage_type}")

    storage_info = STORAGE_IMPLEMENTATIONS[storage_type]
    if storage_name not in storage_info["implementations"]:
        raise ValueError(
            f"Storage implementation '{storage_name}' is not compatible with {storage_type}. "
            f"Compatible implementations are: {', '.join(storage_info['implementations'])}"
        )
