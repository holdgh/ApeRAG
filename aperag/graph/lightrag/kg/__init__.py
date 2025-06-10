# Import sync storage implementations  
try:
    from .neo4j_sync_impl import Neo4JSyncStorage
except ImportError:
    Neo4JSyncStorage = None

try:
    from .postgres_sync_impl import PGSyncKVStorage, PGSyncVectorStorage, PGSyncDocStatusStorage
except ImportError:
    PGSyncKVStorage = None
    PGSyncVectorStorage = None 
    PGSyncDocStatusStorage = None

STORAGE_IMPLEMENTATIONS = {
    "KV_STORAGE": {
        "implementations": [
            "RedisKVStorage",
            "PGKVStorage",
            "PGSyncKVStorage",
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
            "QdrantVectorDBStorage",
        ],
        "required_methods": ["query", "upsert"],
    },
    "DOC_STATUS_STORAGE": {
        "implementations": [
            "PGDocStatusStorage",
            "PGSyncDocStatusStorage",
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

# Storage implementation module mapping
STORAGES = {
    "Neo4JStorage": ".kg.neo4j_impl",
    "Neo4JSyncStorage": ".kg.neo4j_sync_impl",
    "RedisKVStorage": ".kg.redis_impl",
    "PGKVStorage": ".kg.postgres_impl",
    "PGVectorStorage": ".kg.postgres_impl",
    "PGGraphStorage": ".kg.postgres_impl",
    "PGDocStatusStorage": ".kg.postgres_impl",
    "QdrantVectorDBStorage": ".kg.qdrant_impl",
}

# Add sync implementations to storage_dict
if Neo4JSyncStorage is not None:
    STORAGES["Neo4JSyncStorage"] = ".kg.neo4j_sync_impl"

if PGSyncKVStorage is not None:
    STORAGES["PGSyncKVStorage"] = ".kg.postgres_sync_impl"
    
if PGSyncVectorStorage is not None:
    STORAGES["PGSyncVectorStorage"] = ".kg.postgres_sync_impl"
    
if PGSyncDocStatusStorage is not None:
    STORAGES["PGSyncDocStatusStorage"] = ".kg.postgres_sync_impl"

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
