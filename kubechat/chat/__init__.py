
from readers.base_embedding import get_embedding_model


embedding_model, vector_size = get_embedding_model({"model_type": "huggingface"})