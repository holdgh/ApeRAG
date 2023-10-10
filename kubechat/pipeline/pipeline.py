import random
import re
import json
import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict

from langchain import PromptTemplate
from langchain.schema import BaseChatMessageHistory, HumanMessage, AIMessage
from pydantic import BaseModel

from config import settings
from kubechat.context.context import ContextManager
from kubechat.llm.predict import Predictor, PredictorType
from kubechat.llm.prompts import DEFAULT_MODEL_PROMPT_TEMPLATES, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2
from kubechat.pipeline.keyword_extractor import IKExtractor
from kubechat.utils.full_text import search_document
from kubechat.utils.utils import generate_vector_db_collection_name, now_unix_milliseconds, \
    generate_qa_vector_db_collection_name, generate_fulltext_index_name
from query.query import get_packed_answer
from readers.base_embedding import get_embedding_model, get_rerank_model

KUBE_CHAT_DOC_QA_REFERENCES = "|KUBE_CHAT_DOC_QA_REFERENCES|"


logger = logging.getLogger(__name__)


class Message(BaseModel):
    id: str
    query: Optional[str]
    timestamp: Optional[int]
    response: Optional[str]
    references: Optional[List[Dict]]
    collection_id: Optional[str]
    embedding_model: Optional[str]
    embedding_size: Optional[int]
    embedding_score_threshold: Optional[float]
    embedding_topk: Optional[int]
    llm_model: Optional[str]
    llm_prompt_template: Optional[str]
    llm_context_window: Optional[int]


class Pipeline(ABC):
    def __init__(self,
                 bot,
                 collection,
                 history: BaseChatMessageHistory,
                 ):
        self.bot = bot
        self.collection = collection
        self.history = history
        self.collection_id = collection.id
        bot_config = json.loads(self.bot.config)
        self.llm_config = bot_config.get("llm", {})
        self.model = bot_config.get("model", "baichuan-13b")
        self.topk = self.llm_config.get("similarity_topk", 3)
        self.score_threshold = self.llm_config.get("similarity_score_threshold", 0.5)
        self.context_window = self.llm_config.get("context_window", 3500)
        self.prompt_template = self.llm_config.get("prompt_template", None)
        if not self.prompt_template:
            self.prompt_template = DEFAULT_MODEL_PROMPT_TEMPLATES.get(self.model, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2)
        self.prompt = PromptTemplate.from_template(self.prompt_template)

        collection_name = generate_vector_db_collection_name(collection.id)
        self.vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        self.vectordb_ctx["collection"] = collection_name

        config = json.loads(collection.config)
        self.embedding_model_name = config.get("embedding_model", settings.EMBEDDING_MODEL)
        self.embedding_model, self.vector_size = get_embedding_model(self.embedding_model_name)

        self.context_manager = ContextManager(collection_name, self.embedding_model, settings.VECTOR_DB_TYPE,
                                              self.vectordb_ctx)

        qa_collection_name = generate_qa_vector_db_collection_name(self.collection.id)
        self.qa_vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        self.qa_vectordb_ctx["collection"] = qa_collection_name
        self.qa_context_manager = ContextManager(qa_collection_name, self.embedding_model, settings.VECTOR_DB_TYPE,
                                                   self.qa_vectordb_ctx)

    @staticmethod
    def new_human_message(message, message_id):
        return Message(
            id=message_id,
            query=message,
            timestamp=now_unix_milliseconds(),
        )

    def new_ai_message(self, message, message_id, response, references):
        return Message(
            id=message_id,
            query=message,
            response=response,
            timestamp=now_unix_milliseconds(),
            references=references,
            collection_id=self.collection_id,
            embedding_model=self.embedding_model_name,
            embedding_size=self.vector_size,
            embedding_score_threshold=self.score_threshold,
            embedding_topk=self.topk,
            llm_model=self.model,
            llm_prompt_template=self.prompt_template,
            llm_context_window=self.context_window,
        )

    def add_human_message(self, message, message_id):
        if not message_id:
            message_id = str(uuid.uuid4())

        human_msg = self.new_human_message(message, message_id).json(exclude_none=True)
        self.history.add_message(
            HumanMessage(
                content=human_msg,
                additional_kwargs={"role": "human"}
            )
        )

    def add_ai_message(self, message, message_id, response, references):
        ai_msg = self.new_ai_message(message, message_id, response, references).json(exclude_none=True)
        self.history.add_message(
            AIMessage(
                content=ai_msg,
                additional_kwargs={"role": "ai"}
            )
        )

    @abstractmethod
    async def run(self, query, gen_references=False, message_id=""):
        pass


class FakePipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        words_path = kwargs.get("words_path", Path(__file__).parent / "words_dictionary.json")
        with open(words_path) as fd:
            self.words = list(json.loads(fd.read()).keys())

    def sentence_generator(self, batch=1, min_len=3, max_len=10):
        for i in range(batch):
            tokens = []
            for j in range(random.randint(min_len, max_len)):
                tokens.append(random.choice(self.words))
            yield " ".join(tokens)

    async def run(self, message, gen_references=False, message_id=""):
        self.add_human_message(message, message_id)

        response = ""
        for sentence in self.sentence_generator(batch=5, min_len=10, max_len=30):
            if random.sample([True, False], 1):
                sentence += "\n\n"
            yield sentence
            response += sentence

        references = []
        for result in range(3):
            ref = ""
            for sentence in self.sentence_generator(batch=5, min_len=20, max_len=50):
                if random.sample([True, False], 1):
                    sentence += "\n\n"
                ref += sentence
            references.append({
                "score": round(random.uniform(0.5, 0.6), 2),
                "text": ref,
                "metadata": {"source": ref[:20]},
            })

        self.add_ai_message(message, message_id, response, references)

        if gen_references:
            yield KUBE_CHAT_DOC_QA_REFERENCES + json.dumps(references)


class BasePipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, message, gen_reference=False, message_id=""):
        self.add_human_message(message, message_id)

        results = self.context_manager.query(message, self.score_threshold, self.topk)
        context = ""
        if len(results) > 0:
            context = get_packed_answer(results, self.context_window)
        prompt = self.prompt.format(query=message, context=context)

        response = ""
        predictor = Predictor.from_model(self.model, PredictorType.CUSTOM_LLM, **self.llm_config)
        async for msg in predictor.agenerate_stream(prompt):
            yield msg
            response += msg

        references = []
        for result in results:
            references.append({
                "score": result.score,
                "text": result.text,
                "metadata": result.metadata
            })
        self.add_ai_message(message, message_id, response, references)

        if gen_reference:
            yield KUBE_CHAT_DOC_QA_REFERENCES + json.dumps(references)


class QueryRewritePipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(self, message, gen_references=False, message_id=""):
        self.add_human_message(message, message_id)

        references = []
        results = self.qa_context_manager.query(message, score_threshold=0.85, topk=1)
        if len(results) > 0:
            response = results[0].text
            yield response
        else:
            results = self.context_manager.query(message, self.score_threshold, self.topk)
            context = ""
            if len(results) > 0:
                context = get_packed_answer(results, self.context_window)
            prompt = self.prompt.format(query=message, context=context)

            response = ""
            predictor = Predictor.from_model(self.model, PredictorType.CUSTOM_LLM, **self.llm_config)
            async for msg in predictor.agenerate_stream(prompt):
                yield msg
                response += msg

            for result in results:
                references.append({
                    "score": result.score,
                    "text": result.text,
                    "metadata": result.metadata
                })

        self.add_ai_message(message, message_id, response, references)

        if gen_references:
            yield KUBE_CHAT_DOC_QA_REFERENCES + json.dumps(references)


class KeywordPipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ranker = get_rerank_model()

    async def run(self, message, gen_references=False, message_id=""):
        self.add_human_message(message, message_id)

        references = []
        predictor = Predictor.from_model(self.model, PredictorType.CUSTOM_LLM, **self.llm_config)

        results = self.qa_context_manager.query(message, score_threshold=0.9, topk=1)
        if len(results) > 0:
            response = results[0].text
            yield response
        else:
            index = generate_fulltext_index_name(self.collection_id)
            keywords = IKExtractor({"index_name": index, "es_host": settings.ES_HOST}).extract(message)
            logger.info("[%s] extract keywords: %s", message, " | ".join(keywords))

            # find the related documents using keywords
            doc_names = {}
            if keywords:
                docs = search_document(index, keywords, self.topk * 3)
                for doc in docs:
                    doc_names[doc["name"]] = doc["content"]
                    logger.info("[%s] found keyword in document %s", message, doc["name"])

            candidates = []
            results = self.context_manager.query(message, self.score_threshold, self.topk * 6)
            if len(results) > self.topk:
                results = self.ranker.rank(message, results)[:self.topk]
            for result in results:
                if result.metadata["name"] not in doc_names:
                    logger.info("[%s] ignore doc %s not match keywords", message, result.metadata["name"])
                    continue
                candidates.append(result)
            # if no keywords found, fallback to using all results from embedding search
            if not doc_names:
                candidates = results

            context = ""
            if len(candidates) > 0:
                context = get_packed_answer(candidates, self.context_window)
            prompt = self.prompt.format(query=message, context=context)

            response = ""
            async for msg in predictor.agenerate_stream(prompt):
                yield msg
                response += msg

            for result in candidates:
                references.append({
                    "score": result.score,
                    "text": result.text,
                    "metadata": result.metadata
                })

        self.add_ai_message(message, message_id, response, references)

        if gen_references:
            yield KUBE_CHAT_DOC_QA_REFERENCES + json.dumps(references)
