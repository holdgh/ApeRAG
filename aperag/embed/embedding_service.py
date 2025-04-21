from typing import List

import litellm
from langchain.embeddings.base import Embeddings

class EmbeddingService(Embeddings):
    def __init__(self, embedding_backend, embedding_model, embedding_dim,
                 embedding_service_url, embedding_service_api_key, embedding_max_chunks_in_batch):
        self.model = f"{embedding_backend}/{embedding_model}"
        self.api_base = f"{embedding_service_url}"
        self.api_key = f"{embedding_service_api_key}"
        self.max_chunks = embedding_max_chunks_in_batch

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        max_chunks = self.max_chunks if self.max_chunks and self.max_chunks > 0 else len(texts)
        embeddings = []
        for i in range(0, len(texts), max_chunks):
            batch = texts[i:i + max_chunks]
            response = litellm.embedding(
                model=f"{self.model}",
                api_base=self.api_base,
                api_key=self.api_key,
                input=batch,
            )
            embeddings.extend([item["embedding"] for item in response["data"]])

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]