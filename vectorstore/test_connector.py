
from typing import cast
from vectorstore.connector import VectorStoreConnectorAdaptor
from qdrant_client import QdrantClient
from qdrant_client.models import Distance,VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse


def test_qdrant_connector():
    ctx = {"url":"http://localhost", "port":6333, "collection":"test"}
    c = VectorStoreConnectorAdaptor("qdrant", ctx)
    client = cast(QdrantClient, c.connector.client)

    try:
        collection = client.get_collection("test")
    except (UnexpectedResponse):
        client.create_collection(collection_name="test", vectors_config=VectorParams(size=100, distance=Distance.COSINE))

    print(c.connector.client.get_collections())

if __name__ == "__main__":
    test_qdrant_connector()