#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from abc import ABC, abstractmethod
from threading import Lock
from typing import Any, List

import torch
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.embeddings.google_palm import GooglePalmEmbeddings
from langchain.embeddings.huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceInstructEmbeddings,
)
from langchain.embeddings.openai import OpenAIEmbeddings
from llama_index import (
    LangchainEmbedding,
)
from torch import Tensor
from transformers import AutoTokenizer, AutoModel, MT5EncoderModel

from config.settings import EMBEDDING_DEVICE, EMBEDDING_MODEL
from vectorstore.connector import VectorStoreConnectorAdaptor


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
        embeddings = self.model.encode([text])
        return embeddings.tolist()[0]


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
        text = text.replace("\n", " ")
        return self._embed_text(text)


class Multilingual(Embeddings):

    def __init__(self):
        import torch.nn.functional as F
        self.F = F
        model_name = "intfloat/multilingual-e5-large"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    @staticmethod
    def average_pool(last_hidden_states: Tensor,
                     attention_mask: Tensor) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def _embed_text(self, text):
        # Each input text should start with "query: " or "passage: ", even for non-English texts.
        # For tasks other than retrieval, you can simply use the "query: " prefix.
        # input_texts = ['query: how much protein should a female eat',
        #                'query: 南瓜的家常做法',
        #                "passage: As a general guideline, the CDC's average requirement of protein for women ages 19 to 70 is 46 grams per day. But, as you can see from this chart, you'll need to increase that if you're expecting or training for a marathon. Check out the chart below to see how much protein you should be eating each day.",
        #                "passage: 1.清炒南瓜丝 原料:嫩南瓜半个 调料:葱、盐、白糖、鸡精 做法: 1、南瓜用刀薄薄的削去表面一层皮,用勺子刮去瓤 2、擦成细丝(没有擦菜板就用刀慢慢切成细丝) 3、锅烧热放油,入葱花煸出香味 4、入南瓜丝快速翻炒一分钟左右,放盐、一点白糖和鸡精调味出锅 2.香葱炒南瓜 原料:南瓜1只 调料:香葱、蒜末、橄榄油、盐 做法: 1、将南瓜去皮,切成片 2、油锅8成热后,将蒜末放入爆香 3、爆香后,将南瓜片放入,翻炒 4、在翻炒的同时,可以不时地往锅里加水,但不要太多 5、放入盐,炒匀 6、南瓜差不多软和绵了之后,就可以关火 7、撒入香葱,即可出锅"]

        input_texts = [text]

        # Tokenize the input texts
        batch_dict = self.tokenizer(input_texts, max_length=512, padding=True, truncation=True, return_tensors='pt')
        outputs = self.model(**batch_dict)
        embeddings = self.average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
        return embeddings.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        result = []
        for text in texts:
            embedding = self._embed_text(f"passage: {text}")
            result.append(embedding[0])
        return result

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(f"query: {text}")[0]


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
        text = text.replace("\n", " ")
        return self._embed_text(text)


mutex = Lock()
embedding_model_cache = {}


def get_embedding_model(model_type: str, load=True) -> {LangchainEmbedding, int}:
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
        elif model_type == "bge":
            if load:
                model_kwargs = {'device': EMBEDDING_DEVICE}
                # set True to compute cosine similarity
                encode_kwargs = {'normalize_embeddings': True}
                embedding_model = LangchainEmbedding(HuggingFaceBgeEmbeddings(
                    model_name="BAAI/bge-large-zh",
                    model_kwargs=model_kwargs,
                    encode_kwargs=encode_kwargs
                ))
            vector_size = 1024
        elif model_type == "openai":
            if load:
                embedding_model = LangchainEmbedding(OpenAIEmbeddings(max_retries=1, request_timeout=60))
            vector_size = 1536
        elif model_type == "google":
            if load:
                embedding_model = LangchainEmbedding(GooglePalmEmbeddings())
            vector_size = 768
        elif model_type == "bert":
            if load:
                embedding_model = LangchainEmbedding(BertEmbedding())
            vector_size = 1024
        elif model_type == "multilingual":
            if load:
                embedding_model = LangchainEmbedding(Multilingual())
            vector_size = 1024
        elif model_type == "mt5":
            if load:
                embedding_model = LangchainEmbedding(MT5Embedding())
            vector_size = 768
        else:
            raise ValueError("unsupported embedding model ", model_type)

        if embedding_model:
            embedding_model_cache[model_type] = (embedding_model, vector_size)

    return embedding_model, vector_size


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
            embedding_model: LangchainEmbedding,
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
