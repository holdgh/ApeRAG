import random
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
from kubechat.llm.base import Predictor, PredictorType
from kubechat.llm.prompts import DEFAULT_MODEL_PROMPT_TEMPLATES,DEFAULT_MODEL_MEMOTY_PROMPT_TEMPLATES, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2, DEFAULT_CHINESE_PROMPT_TEMPLATE_V3
from kubechat.pipeline.keyword_extractor import IKExtractor
from kubechat.source.utils import async_run
from kubechat.context.full_text import search_document
from kubechat.utils.utils import generate_vector_db_collection_name, now_unix_milliseconds, \
    generate_qa_vector_db_collection_name, generate_fulltext_index_name
from query.query import get_packed_answer
from readers.base_embedding import get_embedding_model, rerank

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
        self.memory = bot_config.get("memory", False)
        self.memory_count = 0
        self.memory_limit_length = bot_config.get("memory_length", 0)
        self.memory_limit_count = bot_config.get("memory_count", 10)
        self.topk = self.llm_config.get("similarity_topk", 3)
        self.enable_keyword_recall = self.llm_config.get("enable_keyword_recall", False)
        self.score_threshold = self.llm_config.get("similarity_score_threshold", 0.5)
        self.context_window = self.llm_config.get("context_window", 3500)
        self.prompt_template = self.llm_config.get("prompt_template", None)
        if not self.prompt_template:
            if self.memory:
                self.prompt_template = DEFAULT_MODEL_MEMOTY_PROMPT_TEMPLATES.get(self.model,DEFAULT_CHINESE_PROMPT_TEMPLATE_V3)
            else:
                self.prompt_template = DEFAULT_MODEL_PROMPT_TEMPLATES.get(self.model, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2)
        self.prompt = PromptTemplate(template=self.prompt_template, input_variables=["query", "context"])
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

        kwargs = {"model": self.model}
        kwargs.update(self.llm_config)
        self.predictor = Predictor.from_model(self.model, PredictorType.CUSTOM_LLM, **kwargs)

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
        async for msg in self.predictor.agenerate_stream(prompt):
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
        vector = self.embedding_model.embed_query(message)
        results = self.qa_context_manager.query(message, score_threshold=0.85, topk=1, vector=vector)
        if len(results) > 0:
            response = results[0].text
            yield response
        else:
            results = self.context_manager.query(message, self.score_threshold, self.topk, vector=vector)
            context = ""
            if len(results) > 0:
                context = get_packed_answer(results, self.context_window)
            prompt = self.prompt.format(query=message, context=context)

            response = ""
            async for msg in self.predictor.agenerate_stream(prompt):
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

    async def filter_by_keywords(self, message, candidates):
        index = generate_fulltext_index_name(self.collection_id)
        async with IKExtractor({"index_name": index, "es_host": settings.ES_HOST}) as extractor:
            keywords = await extractor.extract(message)
            logger.info("[%s] extract keywords: %s", message, " | ".join(keywords))

        # find the related documents using keywords
        docs = await search_document(index, keywords, self.topk * 3)
        if not docs:
            return candidates

        doc_names = {}
        for doc in docs:
            doc_names[doc["name"]] = doc["content"]
            logger.info("[%s] found keyword in document %s", message, doc["name"])

        result = []
        for item in candidates:
            if item.metadata["name"] not in doc_names:
                logger.info("[%s] ignore doc %s not match keywords", message, item.metadata["name"])
                continue
            result.append(item)
        return result

    async def run(self, message, gen_references=False, message_id=""):
        log_prefix = f"{message_id}|{message}"
        logger.info("[%s] start processing", log_prefix)

        references = []
        vector = self.embedding_model.embed_query(message)
        logger.info("[%s] embedding query end", log_prefix)
        results = await async_run(self.qa_context_manager.query, message, score_threshold=0.9, topk=1, vector=vector)
        logger.info("[%s] find relevant qa pairs in vector db end", log_prefix)
        if len(results) > 0:
            response = results[0].text
            yield response
        else:
            results = await async_run(self.context_manager.query, message,
                                      score_threshold=self.score_threshold, topk=self.topk * 6, vector=vector)
            logger.info("[%s] find top %d relevant context in vector db end", log_prefix, len(results))
            if len(results) > 1:
                results = rerank(message, results)
                logger.info("[%s] rerank candidates end", log_prefix)
            else:
                logger.info("[%s] don't need to rerank ", log_prefix)

            candidates = results[:self.topk]
            if self.enable_keyword_recall:
                candidates = self.filter_by_keywords(message, candidates)
                logger.info("[%s] filter keyword end", log_prefix)
            else:
                logger.info("[%s] no need to filter keyword", log_prefix)

            context = ""
            if len(candidates) > 0:
                # 500 is the estimated length of the prompt
                context = get_packed_answer(candidates, max(self.context_window - 500, 0))

            history = []
            if self.memory and len(self.history.messages) > 0:
                history = self.predictor.get_latest_history(
                                messages=self.history.messages,
                                limit_length=max(min(self.context_window-500-len(context),self.memory_limit_length), 0),
                                limit_count=self.memory_limit_count)
                self.memory_count = len(history)

            prompt = self.prompt.format(query=message, context=context)
            logger.info("[%s] final prompt is\n%s", log_prefix, prompt)

            response = ""
            async for msg in self.predictor.agenerate_stream(history, prompt, self.memory):
                yield msg
                response += msg

            for result in candidates:
                references.append({
                    "score": result.score,
                    "text": result.text,
                    "metadata": result.metadata
                })

        self.add_human_message(message, message_id)
        logger.info("[%s] add human message end", log_prefix)

        self.add_ai_message(message, message_id, response, references)
        logger.info("[%s] add ai message end and the pipeline is succeed", log_prefix)

        if gen_references:
            yield KUBE_CHAT_DOC_QA_REFERENCES + json.dumps(references)
