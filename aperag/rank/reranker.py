#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any, List

import aiohttp
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from FlagEmbedding import FlagReranker

from aperag.query.query import DocumentWithScore
from config.settings import (
    RERANK_BACKEND,
    RERANK_SERVICE_MODEL_UID,
    RERANK_SERVICE_URL,
)

default_rerank_model_path = "/data/models/bge-reranker-large"

# Mutex and synchronized decorator (copied for self-containment as requested)
mutex = Lock()
rerank_model_cache = {}


# synchronized decorator
def synchronized(func):
    def wrapper(*args, **kwargs):
        with mutex:
            return func(*args, **kwargs)

    return wrapper


class Ranker(ABC):

    @abstractmethod
    async def rank(self, query, results: List[DocumentWithScore]):
        pass


class RankerService(Ranker):
    def __init__(self):
        if RERANK_BACKEND == "xinference":
            self.ranker = XinferenceRanker()
        elif RERANK_BACKEND == "local":
            self.ranker = FlagCrossEncoderRanker()
        else:
            raise Exception(
                "Unsupported embedding backend")  # Note: Error message refers to embedding backend, might be a typo in original code

    async def rank(self, query, results: List[DocumentWithScore]):
        return await self.ranker.rank(query, results)


class XinferenceRanker(Ranker):
    def __init__(self):
        self.url = f"{RERANK_SERVICE_URL}/v1/rerank"
        self.model_uid = RERANK_SERVICE_MODEL_UID

    async def rank(self, query, results: List[DocumentWithScore]):
        documents = [document.text for document in results]
        request_body = {
            "model": self.model_uid,
            "documents": documents,
            "query": query,
            "return_documents": False,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=request_body) as response:
                response_data = await response.json()
                if response.status != 200:
                    raise RuntimeError(f"Failed to rerank documents, detail: {response_data['detail']}")
                indices = [response['index'] for response in response_data['results']]
                return [results[index] for index in indices]


class ContentRatioRanker(Ranker):
    def __init__(self,
                 query):  # Note: query passed in constructor but not used in rank method? Original code behavior preserved.
        self.query = query

    async def rank(self, query, results: List[DocumentWithScore]):
        results.sort(key=lambda x: (x.metadata.get("content_ratio", 1), x.score), reverse=True)
        return results


class AutoCrossEncoderRanker(Ranker):
    def __init__(self):
        model_path = os.environ.get("RERANK_MODEL_PATH", default_rerank_model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    async def rank(self, query, results: List[DocumentWithScore]):
        pairs = []
        for idx, result in enumerate(results):
            pairs.append((query, result.text))
            result.rank_before = idx

        with torch.no_grad():
            inputs = self.tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
            scores = self.model(**inputs, return_dict=True).logits.view(-1, ).float()
            # Ensure scores is iterable even if only one result
            if not isinstance(scores, (list, torch.Tensor)) or (
                    isinstance(scores, torch.Tensor) and scores.numel() == 1 and len(results) == 1):
                scores = [scores.item()] if isinstance(scores, torch.Tensor) else [scores]
            elif isinstance(scores, torch.Tensor):
                scores = scores.tolist()

            results = [x for _, x in sorted(zip(scores, results), key=lambda k: k[0], reverse=True)]

        return results


class FlagCrossEncoderRanker(Ranker):
    def __init__(self):
        model_path = os.environ.get("RERANK_MODEL_PATH", default_rerank_model_path)
        # self.reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True) #use fp16 can speed up computing
        self.reranker = FlagReranker(model_path)  # use fp16 can speed up computing

    async def rank(self, query, results: List[DocumentWithScore]):
        pairs = []
        max_length = 512
        for idx, result in enumerate(results):
            pairs.append((query[:max_length], result.text[:max_length]))
            result.rank_before = idx

        if not pairs:
            return []

        with torch.no_grad():
            scores = self.reranker.compute_score(pairs, max_length=max_length)
            # FlagReranker returns a single float if only one pair is given
            if isinstance(scores, float):
                scores = [scores]
        results = [x for _, x in sorted(zip(scores, results), key=lambda k: k[0], reverse=True)]

        return results


@synchronized
def get_rerank_model(model_type: str = "bge-reranker-large"):
    # self.reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True) #use fp16 can speed up computing
    # Note: model_type parameter is not currently used to select different RankerService logic, but kept for signature consistency.
    if model_type in rerank_model_cache:
        return rerank_model_cache[model_type]
    model = RankerService()
    rerank_model_cache[model_type] = model
    return model


async def rerank(message, results):
    model = get_rerank_model()
    results = await model.rank(message, results)
    return results