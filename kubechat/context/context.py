import time
from abc import ABC, abstractmethod
from typing import List

import torch
from FlagEmbedding import FlagReranker
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig

from config import settings
from query.query import QueryWithEmbedding, DocumentWithScore
from vectorstore.connector import VectorStoreConnectorAdaptor


class Ranker(ABC):

    @abstractmethod
    def rank(self, query, results: List[DocumentWithScore]):
        pass


class ContentRatioRanker(Ranker):
    def __init__(self, query):
        self.query = query

    def rank(self, query, results: List[DocumentWithScore]):
        results.sort(key=lambda x: (x.metadata.get("content_ratio", 1), x.score), reverse=True)
        return results


class AutoCrossEncoderRanker(Ranker):
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-large', device=settings.EMBEDDING_DEVICE)
        self.model = AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-large', device=settings.EMBEDDING_DEVICE)
        self.model.eval()

    def rank(self, query, results: List[DocumentWithScore]):
        pairs = []
        for idx, result in enumerate(results):
            pairs.append((query, result.text))
            result.rank_before = idx

        with torch.no_grad():
            inputs = self.tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
            scores = self.model(**inputs, return_dict=True).logits.view(-1, ).float()
            results = [x for _, x in sorted(zip(scores, results), reverse=True)]

        return results


class FlagCrossEncoderRanker(Ranker):
    def __init__(self):
        # self.reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True) #use fp16 can speed up computing
        self.reranker = FlagReranker('BAAI/bge-reranker-large')  # use fp16 can speed up computing

    def rank(self, query, results: List[DocumentWithScore]):
        pairs = []
        for idx, result in enumerate(results):
            pairs.append((query, result.text))
            result.rank_before = idx

        with torch.no_grad():
            scores = self.reranker.compute_score(pairs)
            if len(pairs) == 1:
                scores = [scores]
        results = [x for _, x in sorted(zip(scores, results), reverse=True)]

        return results


class ContextManager(ABC):

    def __init__(self, collection_name, embedding_model, vectordb_type, vectordb_ctx):
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.adaptor = VectorStoreConnectorAdaptor(vectordb_type, vectordb_ctx)

    def query(self, query, score_threshold=0.5, topk=3):
        vector = self.embedding_model.embed_query(query)
        query_embedding = QueryWithEmbedding(query=query, top_k=topk, embedding=vector)
        return self.adaptor.connector.search(
            query_embedding,
            collection_name=self.collection_name,
            query_vector=query_embedding.embedding,
            with_vectors=True,
            limit=query_embedding.top_k,
            consistency="majority",
            search_params={"hnsw_ef": 128, "exact": False},
            score_threshold=score_threshold,
        ).results
