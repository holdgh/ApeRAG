from readers.local_path_embedding import LocalPathEmbedding
from vectorstore.connector import VectorStoreConnectorAdaptor

def test_local_path_embedding():
    ctx = {"url":"http://localhost", "port":6333, "collection":"test", "vector_size":768, "timeout": 1000}
    adaptor = VectorStoreConnectorAdaptor("qdrant", ctx)
    lpm = LocalPathEmbedding(adaptor, {"model_type": "huggingface"}, input_dir="/Users/slc/Desktop/Budda")
    lpm.load_data()


test_local_path_embedding()