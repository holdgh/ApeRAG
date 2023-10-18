#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any, List

import torch
from FlagEmbedding import FlagReranker
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.embeddings.google_palm import GooglePalmEmbeddings
from langchain.embeddings.huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceInstructEmbeddings,
)
from langchain.embeddings.openai import OpenAIEmbeddings
from transformers import AutoTokenizer, MT5EncoderModel, AutoModelForSequenceClassification

from config.settings import EMBEDDING_DEVICE, EMBEDDING_MODEL
from query.query import DocumentWithScore
from vectorstore.connector import VectorStoreConnectorAdaptor


class Text2VecEmbedding(Embeddings):
    def __init__(self, **kwargs):
        from text2vec import SentenceModel
        self.model = SentenceModel('shibing624/text2vec-base-chinese', **kwargs)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


class MT5Embedding(Embeddings):
    def __init__(self):
        model_name = "csebuetnlp/mT5_m2o_chinese_simplified_crossSum"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = MT5EncoderModel.from_pretrained(model_name)

    def _embed_text(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs, return_dict=True, output_hidden_states=True)
        r = torch.mean(outputs.hidden_states[-1].squeeze(), dim=0)
        return r.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        result = []
        for text in texts:
            result.append(self._embed_text(text))
        return result

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


class PiccoloEmbedding(Embeddings):

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        os.environ.setdefault("https_proxy", "socks5://127.0.0.1:34001")
        self.model = SentenceTransformer('sensenova/piccolo-large-zh')

    def _embed_text(self, texts):
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [embedding.tolist() for embedding in embeddings]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        result = []
        for text in texts:
            text = text.replace("\n", " ")
            if len(text) > 100:
                text = "结果：" + text
            result.append(text)
        return self._embed_text(result)

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(["查询：" + text])[0]


class MultilingualSentenceTransformer(Embeddings):

    def __init__(self):
        import torch.nn.functional as F

        self.F = F
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('intfloat/multilingual-e5-large')

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        result = []
        for text in texts:
            embeddings = self.model.encode([f"passage: {text}"], normalize_embeddings=True)
            result.append(embeddings.tolist()[0])
        return result

    def embed_query(self, text: str) -> List[float]:
        embeddings = self.model.encode([f"query: {text}"], normalize_embeddings=True)
        return embeddings.tolist()


class BertEmbedding(Embeddings):
    def __init__(self):
        from transformers import BertTokenizer, BertForMaskedLM
        model_name = "IDEA-CCNL/Erlangshen-TCBert-330M-Sentence-Embedding-Chinese"
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertForMaskedLM.from_pretrained(model_name)

    def _embed_text(self, text):
        input_tokens = self.tokenizer(text, add_special_tokens=True, padding=True, return_tensors='pt')
        bert_outputs = self.model(**input_tokens, return_dict=True, output_hidden_states=True)
        r = torch.mean(bert_outputs.hidden_states[-1].squeeze(), dim=0)
        return r.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        result = []
        for text in texts:
            result.append(self._embed_text(text))
        return result

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


default_rerank_model_path = "/data/models/bge-reranker-large"


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
        model_path = os.environ.get("RERANK_MODEL_PATH", default_rerank_model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def rank(self, query, results: List[DocumentWithScore]):
        pairs = []
        for idx, result in enumerate(results):
            pairs.append((query, result.text))
            result.rank_before = idx

        with torch.no_grad():
            inputs = self.tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
            scores = self.model(**inputs, return_dict=True).logits.view(-1, ).float()
            results = [x for _, x in sorted(zip(scores, results), key=lambda k: k[0], reverse=True)]

        return results


class FlagCrossEncoderRanker(Ranker):
    def __init__(self):
        model_path = os.environ.get("RERANK_MODEL_PATH", default_rerank_model_path)
        # self.reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True) #use fp16 can speed up computing
        self.reranker = FlagReranker(model_path)  # use fp16 can speed up computing

    def rank(self, query, results: List[DocumentWithScore]):
        pairs = []
        for idx, result in enumerate(results):
            pairs.append((query, result.text))
            result.rank_before = idx

        with torch.no_grad():
            scores = self.reranker.compute_score(pairs)
            if len(pairs) == 1:
                scores = [scores]
        results = [x for _, x in sorted(zip(scores, results), key=lambda k: k[0], reverse=True)]

        return results


mutex = Lock()
embedding_model_cache = {}
rerank_model_cache = {}


# synchronized decorator
def synchronized(func):
    def wrapper(*args, **kwargs):
        with mutex:
            return func(*args, **kwargs)
    return wrapper


@synchronized
def get_rerank_model(model_type: str = "bge-reranker-large"):
    # self.reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True) #use fp16 can speed up computing
    if model_type in rerank_model_cache:
        return rerank_model_cache[model_type]
    model = FlagCrossEncoderRanker()  # use fp16 can speed up computing
    rerank_model_cache[model_type] = model
    return model


@synchronized
def get_embedding_model(model_type: str, load=True, **kwargs) -> {Embeddings, int}:
    embedding_model = None
    vector_size = 0

    if model_type in embedding_model_cache:
        return embedding_model_cache[model_type]

    if not model_type or model_type == "huggingface":
        if load:
            model_kwargs = {'device': EMBEDDING_DEVICE}
            embedding_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-mpnet-base-v2",
                model_kwargs=model_kwargs,
            )
        vector_size = 768
    elif model_type == "huggingface_instruct":
        if load:
            model_kwargs = {'device': EMBEDDING_DEVICE}
            embedding_model = HuggingFaceInstructEmbeddings(
                model_name="hkunlp/instructor-large",
                model_kwargs=model_kwargs,
            )
        vector_size = 768
    elif model_type == "text2vec":
        if load:
            embedding_model = Text2VecEmbedding(device=EMBEDDING_DEVICE)
        vector_size = 768
    elif model_type == "bge":
        if load:
            model_kwargs = {'device': EMBEDDING_DEVICE}
            # set True to compute cosine similarity
            encode_kwargs = {'normalize_embeddings': True}
            embedding_model = HuggingFaceBgeEmbeddings(
                model_name="BAAI/bge-large-zh",
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
        vector_size = 1024
    elif model_type == "openai":
        if load:
            embedding_model = OpenAIEmbeddings(max_retries=1, request_timeout=60)
        vector_size = 1536
    elif model_type == "google":
        if load:
            embedding_model = GooglePalmEmbeddings()
        vector_size = 768
    elif model_type == "bert":
        if load:
            embedding_model = BertEmbedding()
        vector_size = 1024
    elif model_type == "multilingual":
        if load:
            embedding_model = MultilingualSentenceTransformer()
        vector_size = 1024
    elif model_type == "mt5":
        if load:
            embedding_model = MT5Embedding()
        vector_size = 768
    elif model_type == "piccolo":
        if load:
            embedding_model = PiccoloEmbedding()
        vector_size = 1024
    else:
        raise ValueError("unsupported embedding model ", model_type)

    if embedding_model:
        embedding_model_cache[model_type] = (embedding_model, vector_size)

    return embedding_model, vector_size


def rerank(message, results):
    model = get_rerank_model()
    return model.rank(message, results)


def get_collection_embedding_model(collection):
    config = json.loads(collection.config)
    model_name = config.get("embedding_model", "text2vec")
    return get_embedding_model(model_name)


# preload embedding model will cause model hanging, so we load it when first time use
# get_default_embedding_model()


class DocumentBaseEmbedding(ABC):
    def __init__(
            self,
            vector_store_adaptor: VectorStoreConnectorAdaptor,
            embedding_model: Embeddings,
            vector_size: int,
            **kwargs: Any,
    ) -> None:
        self.connector = vector_store_adaptor.connector
        if embedding_model is None:
            self.embedding, self.vector_size = get_embedding_model(EMBEDDING_MODEL)
        else:
            self.embedding, self.vector_size = embedding_model, vector_size
        self.client = vector_store_adaptor.connector.client

    @abstractmethod
    def load_data(self):
        pass
