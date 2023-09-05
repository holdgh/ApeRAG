from abc import ABC

from query.query import QueryWithEmbedding
from vectorstore.connector import VectorStoreConnectorAdaptor


class RankingStrategy(ABC):
    def sort(self, results):
        pass


class ContextManager(ABC):

    def __init__(self, collection_name, embedding_model, vectordb_type, vectordb_ctx):
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.adaptor = VectorStoreConnectorAdaptor(vectordb_type, vectordb_ctx)

    def query(self, query, score_threshold=0.5, topk=3, recall_factor=1):
        vector = self.embedding_model.embed_query(query)
        query_embedding = QueryWithEmbedding(query=query, top_k=topk*recall_factor, embedding=vector)
        results = self.adaptor.connector.search(
            query_embedding,
            collection_name=self.collection_name,
            query_vector=query_embedding.embedding,
            with_vectors=True,
            limit=query_embedding.top_k,
            consistency="majority",
            search_params={"hnsw_ef": 128, "exact": False},
            score_threshold=score_threshold,
        )
        # results.results.sort(key=lambda x: (x.metadata.get("content_ratio", 1), x.score), reverse=True)
        return results.results[:topk]
