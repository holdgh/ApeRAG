from config.settings import VECTOR_DB_TYPE

from vectorstore.connector import VectorStoreConnectorAdaptor
from vectorstore.qdrant_connector import QdrantVectorStoreConnector


def get_local_vector_db_connector(db_type: str) -> VectorStoreConnectorAdaptor:
    # todo: specify the collection for different user
    return VectorStoreConnectorAdaptor(db_type, ctx={"url": "http://localhost", "port": 6333, "collection": "test"})


vector_db_connector = get_local_vector_db_connector(VECTOR_DB_TYPE)
