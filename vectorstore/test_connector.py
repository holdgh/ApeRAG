
from typing import cast

from pymilvus import MilvusClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance,VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse
from chromadb import Client as ChromaClient
from vectorstore.connector import VectorStoreConnectorAdaptor
from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)

def test_qdrant_connector():
    ctx = {"url":"http://localhost", "port":6333, "collection":"test"}
    c = VectorStoreConnectorAdaptor("qdrant", ctx)
    client = cast(QdrantClient, c.connector.client)

    try:
        collection = client.get_collection("test")
    except (UnexpectedResponse):
        client.create_collection(collection_name="test", vectors_config=VectorParams(size=100, distance=Distance.COSINE))

    print(c.connector.client.get_collections())

def test_milvus_connector():
    ctx = {"url":"http://localhost", "port":19530, "collection":"test"}
    c = VectorStoreConnectorAdaptor("milvus", ctx)
    client = cast(MilvusClient, c.connector.client)
    fields = [
        FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=100),
        FieldSchema(name="random", dtype=DataType.DOUBLE),
        FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=8)
    ]

    schema = CollectionSchema(fields, "hello_milvus is the simplest demo to introduce the APIs")
    print("Create collection `hello_milvus`")
    hello_milvus = Collection("hello_milvus", schema, consistency_level="Strong")
    has = utility.has_collection("hello_milvus")
    print(f"Does collection hello_milvus exist in Milvus: {has}")
    utility.drop_collection("hello_milvus")
    has = utility.has_collection("hello_milvus")
    print(f"drop collection \nDoes collection hello_milvus exist in Milvus after drop: {has}")

def test_chroma_connector():
    ctx = {"collection_name": "test"}
    c = VectorStoreConnectorAdaptor("chroma", ctx)
    client = cast(ChromaClient, c.connector.client)

    collection = client.get_or_create_collection(name="test")

    print(c.connector.client.get_collection(name="test"))

if __name__ == "__main__":
    test_chroma_connector()