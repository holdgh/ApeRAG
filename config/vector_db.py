from config.settings import VECTOR_DB_TYPE, VECTOR_DB_CONTEXT

from vectorstore.connector import VectorStoreConnectorAdaptor
from vectorstore.qdrant_connector import QdrantVectorStoreConnector


def get_vector_db_connector(collection: str) -> VectorStoreConnectorAdaptor:
    # todo: specify the collection for different user
    # one person one collection
    ctx = VECTOR_DB_CONTEXT
    ctx["collection"] = collection
    return VectorStoreConnectorAdaptor(VECTOR_DB_TYPE, ctx=ctx)


# vector_db_connector = get_local_vector_db_connector(VECTOR_DB_TYPE)
