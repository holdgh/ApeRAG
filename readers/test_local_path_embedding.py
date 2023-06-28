from typing import cast
from readers.local_path_embedding import LocalPathEmbedding
from vectorstore.connector import VectorStoreConnectorAdaptor
from readers.base_embedding import get_embedding_model
from qdrant_client import QdrantClient

def test_local_path_embedding():
    ctx = {"url":"http://localhost", "port":6333, "collection":"test", "vector_size":768, "distance":"Cosine", "timeout": 1000}
    adaptor = VectorStoreConnectorAdaptor("qdrant", ctx)
    lpm = LocalPathEmbedding(adaptor, {"model_type": "huggingface"}, input_dir="/path/to/your/document/")
    lpm.load_data()

def test_embedding_query(query: str):
    ctx = {"url":"http://localhost", "port":6333, "collection":"test", "vector_size":768, "distance":"Cosine", "timeout": 1000}
    adaptor = VectorStoreConnectorAdaptor("qdrant", ctx)
    embedding, vector_size = get_embedding_model({"model_type": "huggingface"})
    vector = embedding.get_query_embedding(query)
    client = cast(QdrantClient, adaptor.connector.client)
    hits = client.search(
        collection_name="test",
        query_vector=vector,
        with_vectors=True,
        limit=5,
        consistency="majority",
        search_params={"hnsw_ef":128, "exact":False},
        )

    print("hits:", hits)


#test_local_path_embedding()
test_embedding_query("your query is here")