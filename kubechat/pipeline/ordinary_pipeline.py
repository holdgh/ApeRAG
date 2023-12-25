import asyncio
import logging
import random
import re

from langchain import PromptTemplate
from kubechat.utils.utils import now_unix_milliseconds
from kubechat.pipeline.base_pipeline import Pipeline, Message, KUBE_CHAT_RELATED_QUESTIONS
from kubechat.llm.prompts import ORDINARY_TEMPLATE, ORDINARY_MEMORY_TEMPLATE, ORDINARY_FILE_TEMPLATE

logger = logging.getLogger(__name__)


class OrdinaryPipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.prompt_template=None
        if not self.prompt_template:
            if self.memory:
                self.prompt_template = ORDINARY_MEMORY_TEMPLATE
            else:
                self.prompt_template = ORDINARY_TEMPLATE
        self.prompt = PromptTemplate(template=self.prompt_template, input_variables=["query"])
        self.file_prompt = PromptTemplate(template=ORDINARY_FILE_TEMPLATE,
                                          input_variables=["query", "context"])

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

    async def generate_related_question(self, related_question_prompt):
        related_question = ""
        async for msg in self.related_question_predictor.agenerate_stream([], related_question_prompt):
            related_question += msg
        return related_question

    async def run(self, message, gen_references=False, message_id="", file=None):
        log_prefix = f"{message_id}|{message}"
        logger.info("[%s] start processing", log_prefix)

        related_questions = []
        response = ""

        if self.oops != "":
            response = self.oops
            yield self.oops
            need_generate_answer = False
        if self.welcome_question != []:
            if len(self.welcome_question) >= 3:
                related_questions = random.sample(self.welcome_question, 3)
                need_related_question = False
            else:
                related_questions = self.welcome_question

        context = file if file else ""
        if len(context) > self.context_window - 500:
            context = context[:len(self.context_window) - 500]

        if self.use_related_question and need_related_question:
            related_question_prompt = self.related_question_prompt.format(query=message, context=context)
            related_question_task = asyncio.create_task(self.generate_related_question(related_question_prompt))

        if need_generate_answer:
            history = []
            messages = await self.history.messages
            if self.memory and len(messages) > 0:
                history = self.predictor.get_latest_history(
                    messages=messages,
                    limit_length=max(min(self.context_window - 500 - len(context), self.memory_limit_length), 0),
                    limit_count=self.memory_limit_count,
                    use_ai_memory=self.use_ai_memory)
                self.memory_count = len(history)

            if context:
                prompt = self.file_prompt.format(query=message, context=context)
            else:
                prompt = self.prompt.format(query=message)
            logger.info("[%s] final prompt is\n%s", log_prefix, prompt)

            async for msg in self.predictor.agenerate_stream(history, prompt, self.memory):
                yield msg
                response += msg

            await self.add_human_message(message, message_id)
            logger.info("[%s] add human message end", log_prefix)

            await self.add_ai_message(message, message_id, response, references=[])
            logger.info("[%s] add ai message end and the pipeline is succeed", log_prefix)

            if self.use_related_question:
                if need_related_question:
                    related_question_generate = await related_question_task
                    related_question = re.sub(r'\n+', '\n', related_question_generate).split('\n')
                    for i, question in enumerate(related_question):
                        match = re.match(r"\s*-\s*(.*)", question)
                        if match:
                            question = match.group(1)
                        match = re.match(r"\s*\d+\.\s*(.*)", question)
                        if match:
                            question = match.group(1)
                        related_question[i] = question
                    related_questions.extend(related_question)
                yield KUBE_CHAT_RELATED_QUESTIONS + str(related_questions[:3])
