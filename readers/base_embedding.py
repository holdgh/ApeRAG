#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from abc import ABC, abstractmethod
from threading import Lock, Thread
from typing import Any, Dict, List

from langchain.embeddings.base import Embeddings
from langchain.embeddings.google_palm import GooglePalmEmbeddings
from langchain.embeddings.huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceInstructEmbeddings,
)
from langchain.embeddings.openai import OpenAIEmbeddings
from llama_index import (
    LangchainEmbedding,
    PromptHelper,
    ServiceContext,
    StorageContext,
    download_loader,
)

from vectorstore.connector import VectorStoreConnectorAdaptor
from config.settings import EMBEDDING_DEVICE, EMBEDDING_MODEL


class Text2VecEmbedding(Embeddings):
    def __init__(self):
        from text2vec import SentenceModel
        self.model = SentenceModel('shibing624/text2vec-base-chinese', device=EMBEDDING_DEVICE)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        text = text.replace("\n", " ")
        return self.model.encode(text)


mutex = Lock()
default_embedding_model, default_vector_size = None, 0
embedding_model_cache = {}


def get_embedding_model(
    model_type: str, load=True
) -> {LangchainEmbedding, int}:
    embedding_model = None
    vector_size = 0

    with mutex:
        if model_type in embedding_model_cache:
            return embedding_model_cache[model_type]

        if not model_type or model_type == "huggingface":
            if load:
                model_kwargs = {'device': EMBEDDING_DEVICE}
                embedding_model = LangchainEmbedding(
                    HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-mpnet-base-v2",
                        model_kwargs=model_kwargs,
                    )
                )
            vector_size = 768
        elif model_type == "huggingface_instruct":
            if load:
                model_kwargs = {'device': EMBEDDING_DEVICE}
                embedding_model = LangchainEmbedding(
                    HuggingFaceInstructEmbeddings(
                        model_name="hkunlp/instructor-large",
                        model_kwargs=model_kwargs,
                    )
                )
            vector_size = 768
        elif model_type == "text2vec":
            if load:
                embedding_model = LangchainEmbedding(Text2VecEmbedding())
            vector_size = 768
        elif model_type == "openai":
            if load:
                embedding_model = LangchainEmbedding(OpenAIEmbeddings(max_retries=1, request_timeout=60))
            vector_size = 1536
        elif model_type == "google":
            if load:
                embedding_model = LangchainEmbedding(GooglePalmEmbeddings())
            vector_size = 768
        else:
            raise ValueError("unsupported embedding model ", model_type)

        if embedding_model:
            embedding_model_cache[model_type] = (embedding_model, vector_size)

    return embedding_model, vector_size


def get_default_embedding_model(load=True) -> {LangchainEmbedding, int}:
    global default_embedding_model, default_vector_size
    with mutex:
        if default_embedding_model is None:
            default_embedding_model, default_vector_size = get_embedding_model(
                EMBEDDING_MODEL, load
            )
    return default_embedding_model, default_vector_size


def get_collection_embedding_model(collection):
    config = json.loads(collection.config)
    model_name = config.get("embedding_model", "text2vec")
    return get_embedding_model(model_name)

# preload embedding model will cause model hanging, so we load it when first time use
# get_default_embedding_model()


class DocumentBaseEmbedding(ABC):
    def __init__(
        self,
        uri_path,
        vector_store_adaptor: VectorStoreConnectorAdaptor,
        embedding_model: LangchainEmbedding,
        vector_size: int,
        **kwargs: Any,
    ) -> None:
        self.uri_path = uri_path
        self.connector = vector_store_adaptor.connector
        if embedding_model is None:
            self.embedding, self.vector_size = get_default_embedding_model()
        else:
            self.embedding, self.vector_size = embedding_model, vector_size
        self.client = vector_store_adaptor.connector.client

    @abstractmethod
    def load_data(self):
        pass

    def set_vector_store_adaptor(
        self, vector_store_adaptor: VectorStoreConnectorAdaptor
    ):
        self.connector = vector_store_adaptor.connector
        self.client = vector_store_adaptor.connector.client

    def embed_query(self, query: str) -> List[float]:
        query = query.replace("\n", " ")
        return self.embedding.get_query_embedding(query)
