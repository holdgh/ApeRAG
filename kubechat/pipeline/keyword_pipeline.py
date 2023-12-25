import re
import json
import asyncio
import logging

from config import settings
from langchain import PromptTemplate
from query.query import get_packed_answer
from readers.base_embedding import rerank

from kubechat.source.utils import async_run
from kubechat.pipeline.base_pipeline import Pipeline
from kubechat.pipeline.keyword_extractor import IKExtractor
from kubechat.context.full_text import search_document
from kubechat.utils.utils import generate_fulltext_index_name
from kubechat.llm.prompts import DEFAULT_MODEL_MEMOTY_PROMPT_TEMPLATES, DEFAULT_MODEL_PROMPT_TEMPLATES, \
    DEFAULT_CHINESE_PROMPT_TEMPLATE_V2, DEFAULT_CHINESE_PROMPT_TEMPLATE_V3

logger = logging.getLogger(__name__)

KUBE_CHAT_DOC_QA_REFERENCES = "|KUBE_CHAT_DOC_QA_REFERENCES|"
KUBE_CHAT_RELATED_QUESTIONS = "|KUBE_CHAT_RELATED_QUESTIONS|"


class KeywordPipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.prompt_template:
            if self.memory:
                self.prompt_template = DEFAULT_MODEL_MEMOTY_PROMPT_TEMPLATES.get(self.model,
                                                                                 DEFAULT_CHINESE_PROMPT_TEMPLATE_V3)
            else:
                self.prompt_template = DEFAULT_MODEL_PROMPT_TEMPLATES.get(self.model,
                                                                          DEFAULT_CHINESE_PROMPT_TEMPLATE_V2)
        self.prompt = PromptTemplate(template=self.prompt_template, input_variables=["query", "context"])

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

    async def generate_related_question(self, related_question_prompt):
        related_question = ""
        async for msg in self.related_question_predictor.agenerate_stream([], related_question_prompt):
            related_question += msg
        return related_question

    async def generate_hyde_message(self, message):
        hyde_message = ""
        prompt = "写一篇文章回答这个问题: " + message
        async for msg in self.predictor.agenerate_stream([], prompt, []):
            hyde_message += msg
        logger.info("hyde_message： [%s]", hyde_message)
        return hyde_message

    async def run(self, message, gen_references=False, message_id=""):
        log_prefix = f"{message_id}|{message}"
        logger.info("[%s] start processing", log_prefix)

        references = []
        response = ""
        # hyde_task = asyncio.create_task(self.generate_hyde_message(message))
        vector = self.embedding_model.embed_query(message)
        logger.info("[%s] embedding query end", log_prefix)
        results = await async_run(self.qa_context_manager.query, message, score_threshold=0.9, topk=1, vector=vector)
        logger.info("[%s] find relevant qa pairs in vector db end", log_prefix)
        if len(results) > 0:
            response = results[0].text
            yield response

            if self.use_related_question:
                related_question_prompt = self.related_question_prompt.format(query=message, context=response)
                related_question_task = asyncio.create_task(self.generate_related_question(related_question_prompt))

        else:
            results = await async_run(self.context_manager.query, message,
                                      score_threshold=self.score_threshold, topk=self.topk * 6, vector=vector)
            logger.info("[%s] find top %d relevant context in vector db end", log_prefix, len(results))
            # hyde_message = await hyde_task
            # new_vector = self.embedding_model.embed_query(hyde_message)
            # results2 = await async_run(self.context_manager.query, message,
            #                           score_threshold=self.score_threshold, topk=self.topk * 6, vector=new_vector)
            # results_set = set([result.text for result in results])
            # results.extend(result for result in results2 if result.text not in results_set)
            if len(results) > 1:
                results = rerank(message, results)
                logger.info("[%s] rerank candidates end", log_prefix)
            else:
                logger.info("[%s] don't need to rerank ", log_prefix)

            candidates = results[:self.topk]
            if self.enable_keyword_recall:
                candidates = await self.filter_by_keywords(message, candidates)
                logger.info("[%s] filter keyword end", log_prefix)
            else:
                logger.info("[%s] no need to filter keyword", log_prefix)

            need_generate_answer = True
            need_related_question = True

            context = ""
            if len(candidates) > 0:
                # 500 is the estimated length of the prompt
                context = get_packed_answer(candidates, max(self.context_window - 500, 0))
            else:
                if self.oops != "":
                    response = self.oops
                    yield self.oops
                    need_generate_answer = False
                if self.welcome_question != []:
                    yield KUBE_CHAT_RELATED_QUESTIONS + str(self.welcome_question)
                    need_related_question = False

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

                prompt = self.prompt.format(query=message, context=context)
                logger.info("[%s] final prompt is\n%s", log_prefix, prompt)

                async for msg in self.predictor.agenerate_stream(history, prompt, self.memory):
                    yield msg
                    response += msg

                for result in candidates:
                    references.append({
                        "score": result.score,
                        "text": result.text,
                        "metadata": result.metadata
                    })

        await self.add_human_message(message, message_id)
        logger.info("[%s] add human message end", log_prefix)

        await self.add_ai_message(message, message_id, response, references)
        logger.info("[%s] add ai message end and the pipeline is succeed", log_prefix)

        if self.use_related_question and need_related_question:
            related_question = await related_question_task
            related_question = re.sub(r'\n+', '\n', related_question).split('\n')
            for i, question in enumerate(related_question):
                match = re.match(r"\s*-\s*(.*)", question)
                if match:
                    question = match.group(1)
                match = re.match(r"\s*\d+\.\s*(.*)", question)
                if match:
                    question = match.group(1)
                related_question[i] = question
            yield KUBE_CHAT_RELATED_QUESTIONS + str(related_question[:3])

        if gen_references:
            yield KUBE_CHAT_DOC_QA_REFERENCES + json.dumps(references)
