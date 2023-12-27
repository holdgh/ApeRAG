import json
import uuid
from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from langchain import PromptTemplate
from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel
from kubechat.chat.history.base import BaseChatMessageHistory
from kubechat.llm.base import Predictor, PredictorType
from kubechat.llm.prompts import RELATED_QUESTIONS_TEMPLATE
from kubechat.utils.utils import  now_unix_milliseconds


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


KUBE_CHAT_DOC_QA_REFERENCES = "|KUBE_CHAT_DOC_QA_REFERENCES|"
KUBE_CHAT_RELATED_QUESTIONS = "|KUBE_CHAT_RELATED_QUESTIONS|"


class Pipeline(ABC):
    def __init__(self,
                 bot,
                 collection,
                 history: BaseChatMessageHistory,
                 ):
        self.bot = bot
        self.collection = collection
        self.history = history
        bot_config = json.loads(self.bot.config)
        self.llm_config = bot_config.get("llm", {})
        self.model = bot_config.get("model", "baichuan-13b")
        self.memory = bot_config.get("memory", False)
        self.memory_count = 0
        self.memory_limit_length = bot_config.get("memory_length", 0)
        self.memory_limit_count = bot_config.get("memory_count", 10)
        self.use_ai_memory = bot_config.get("use_ai_memory", True)
        self.topk = self.llm_config.get("similarity_topk", 3)
        self.enable_keyword_recall = self.llm_config.get("enable_keyword_recall", False)
        self.score_threshold = self.llm_config.get("similarity_score_threshold", 0.5)
        self.context_window = self.llm_config.get("context_window", 3500)
        self.use_related_question = bot_config.get("use_related_question", False)

        welcome = bot_config.get("welcome", {})
        faq = welcome.get("faq", [])
        self.welcome_question = []
        for qa in faq:
            self.welcome_question.append(qa["question"])
        self.oops = welcome.get("oops", "")

        if self.memory:
            self.prompt_template = self.llm_config.get("memory_prompt_template", None)
        else:
            self.prompt_template = self.llm_config.get("prompt_template", None)

        kwargs = {"model": self.model}
        kwargs.update(self.llm_config)
        self.predictor = Predictor.from_model(self.model, PredictorType.CUSTOM_LLM, **kwargs)

        if self.use_related_question:
            self.related_question_prompt = PromptTemplate(template=RELATED_QUESTIONS_TEMPLATE,
                                                          input_variables=["query", "context"])
            kwargs = {}
            self.related_question_predictor = Predictor.from_model("gpt-4-1106-preview", **kwargs)

    @staticmethod
    async def new_human_message(message, message_id):
        return Message(
            id=message_id,
            query=message,
            timestamp=now_unix_milliseconds(),
        )

    async def new_ai_message(self, message, message_id, response, references):
        pass

    async def add_human_message(self, message, message_id):
        if not message_id:
            message_id = str(uuid.uuid4())

        human_msg = await (self.new_human_message(message, message_id))
        human_msg = human_msg.json(exclude_none=True)
        await self.history.add_message(
            HumanMessage(
                content=human_msg,
                additional_kwargs={"role": "human"}
            )
        )

    async def add_ai_message(self, message, message_id, response, references):
        ai_msg = await (self.new_ai_message(message, message_id, response, references))
        ai_msg = ai_msg.json(exclude_none=True)
        await self.history.add_message(
            AIMessage(
                content=ai_msg,
                additional_kwargs={"role": "ai"}
            )
        )

    @abstractmethod
    async def run(self, query, gen_references=False, message_id=""):
        pass
