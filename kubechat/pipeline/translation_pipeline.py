import json
from langchain import PromptTemplate
from kubechat.llm.base import Predictor, PredictorType
from kubechat.llm.prompts import CHINESE_TRANSLATION_MEMORY_TEMPLATE, CHINESE_TRANSLATION_TEMPLATE
from kubechat.pipeline.base_pipeline import Pipeline, Message
import logging
from kubechat.chat.history.base import BaseChatMessageHistory
from kubechat.utils.utils import now_unix_milliseconds

logger = logging.getLogger(__name__)

KUBE_CHAT_DOC_QA_REFERENCES = "|KUBE_CHAT_DOC_QA_REFERENCES|"
KUBE_CHAT_RELATED_QUESTIONS = "|KUBE_CHAT_RELATED_QUESTIONS|"


class TranslationPipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prompt_template=None
        if not self.prompt_template:
            if self.memory:
                self.prompt_template = CHINESE_TRANSLATION_MEMORY_TEMPLATE
            else:
                self.prompt_template = CHINESE_TRANSLATION_TEMPLATE
        self.prompt = PromptTemplate(template=self.prompt_template, input_variables=["query"])

    async def new_ai_message(self, message, message_id, response, references):
        return Message(
            id=message_id,
            query=message,
            response=response,
            timestamp=now_unix_milliseconds(),
            references=references,
            llm_model=self.model,
            llm_prompt_template=self.prompt_template,
            llm_context_window=self.context_window,
        )

    async def run(self, message, gen_references=False, message_id=""):
        log_prefix = f"{message_id}|{message}"
        logger.info("[%s] start processing", log_prefix)

        response = ""
        history = []
        context = ""
        messages = await self.history.messages
        if self.memory and len(messages) > 0:
            history = self.predictor.get_latest_history(
                messages=messages,
                limit_length=max(min(self.context_window - 500 - len(context), self.memory_limit_length), 0),
                limit_count=self.memory_limit_count,
                use_ai_memory=self.use_ai_memory)
            self.memory_count = len(history)

        # prompt = self.prompt.format(query=message, context=context)
        prompt = self.prompt.format(query=message)
        logger.info("[%s] final prompt is\n%s", log_prefix, prompt)

        async for msg in self.predictor.agenerate_stream(history, prompt, self.memory):
            yield msg
            response += msg

        await self.add_human_message(message, message_id)
        logger.info("[%s] add human message end", log_prefix)

        await self.add_ai_message(message, message_id, response, references=[])
        logger.info("[%s] add ai message end and the pipeline is succeed", log_prefix)
