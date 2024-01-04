import asyncio
import logging
import random
import re

from nltk import tokenize
from langchain import PromptTemplate

from kubechat.llm.prompts import COMMON_FILE_TEMPLATE, COMMON_MEMORY_TEMPLATE
from kubechat.pipeline.base_pipeline import KUBE_CHAT_RELATED_QUESTIONS, Message, Pipeline
from kubechat.utils.utils import now_unix_milliseconds

logger = logging.getLogger(__name__)


class CommonPipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.prompt_template:
            self.prompt_template = COMMON_MEMORY_TEMPLATE
        self.prompt = PromptTemplate(template=self.prompt_template, input_variables=["query"])
        self.file_prompt = PromptTemplate(template=COMMON_FILE_TEMPLATE, input_variables=["query", "context"])

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

    def split_file(self, file, max_length):
        contexts = []
        pattern = re.compile(r'[。？！，\.?!,]')
        start = 0

        while start < len(file):
            end = min(start + max_length, len(file))

            if end == len(file):
                contexts.append(file[start:end])
                break

            # ensure the last part of this context is semantically complete
            match = pattern.search(file, start, end)
            if match:
                end = match.end()
            else:
                space_position = file.rfind(' ', start, end)
                if space_position != -1:
                    end = space_position

            contexts.append(file[start:end])
            start = end

        return contexts

    def split_file2(self, file, max_length):
        contexts = []
        sentences = tokenize.sent_tokenize(file)

        current_context = ""
        for sentence in sentences:
            if len(current_context) + len(sentence) <= max_length:
                current_context += sentence + " "
            else:
                contexts.append(current_context)
                current_context = sentence + " "

        if current_context:
            contexts.append(current_context)

        return contexts

    async def run(self, message, gen_references=False, message_id="", file=None):
        log_prefix = f"{message_id}|{message}"
        logger.info("[%s] start processing", log_prefix)

        related_questions = []
        response = ""

        need_related_question = True

        if self.welcome_question != []:
            if len(self.welcome_question) >= 3:
                related_questions = random.sample(self.welcome_question, 3)
                need_related_question = False
            else:
                related_questions = self.welcome_question

        contexts = []
        # file = "test long file"

        if file:
            contexts = self.split_file2(file, max_length=self.context_window - 500)
        else:
            contexts.append("")

        if self.use_related_question and need_related_question:
            related_question_prompt = self.related_question_prompt.format(query=message, context=contexts[0])
            related_question_task = asyncio.create_task(self.generate_related_question(related_question_prompt))

        for context in contexts:
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
                # skip unused part in the large file
                if file and msg == "不知道":
                    continue
                yield msg
                response += msg

            if not response:
                yield "我无法根据文件中的信息回答这个问题"

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
