#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from vectorstore.connector import VectorStoreConnectorAdaptor
from langchain.embeddings.huggingface import HuggingFaceEmbeddings, HuggingFaceInstructEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings.google_palm import GooglePalmEmbeddings
from llama_index import (
    LangchainEmbedding,
    ServiceContext,
    StorageContext,
    download_loader,
    PromptHelper
)
from threading import Thread, Lock


def get_embedding_model(embedding_config: Dict[str, Any]) -> {LangchainEmbedding, int}:
    type = embedding_config["model_type"]
    embedding_model = None
    vector_size = 0

    if not type or type == "huggingface":
        embedding_model = LangchainEmbedding(
            HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"))
        vector_size = 768
    elif type == "huggingface_instruct":
        embedding_model = LangchainEmbedding(
            HuggingFaceInstructEmbeddings("hkunlp/instructor-large"))
        vector_size = 768
    elif type == "openai":
        embedding_model = LangchainEmbedding(OpenAIEmbeddings())
        vector_size = 1536
    elif type == "google":
        embedding_model = LangchainEmbedding(GooglePalmEmbeddings())
        vector_size = 768
    else:
        raise ValueError("unsupported embedding model ", type)

    return embedding_model, vector_size


mutex = Lock()
default_embedding_model, default_vector_size = None, 0


def get_default_embedding_model() -> {LangchainEmbedding, int}:
    global default_embedding_model, default_vector_size
    with mutex:
        if default_embedding_model is None:
            default_embedding_model, default_vector_size = get_embedding_model({"model_type": "huggingface"})
    return default_embedding_model, default_vector_size


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

    def set_vector_store_adaptor(self, vector_store_adaptor: VectorStoreConnectorAdaptor):
        self.connector = vector_store_adaptor.connector
        self.client = vector_store_adaptor.connector.client

    def embed_query(self, query: str) -> List[float]:
        query = query.replace("\n", " ")
        return self.embedding.get_query_embedding(query)