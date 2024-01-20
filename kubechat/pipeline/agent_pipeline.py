import asyncio
import json
import logging
import random
import re

from langchain import PromptTemplate
from langchain.output_parsers.json import parse_json_markdown

from config import settings
from kubechat.agent.tool import SeleceTools
from kubechat.context.context import ContextManager
from kubechat.context.full_text import search_document
from kubechat.llm.prompts import (
    FORMAT_INSTRUCTIONS_CHINESE,
    QA_SELECT_PROMPT,
    SUFFIX_CHINESE,
    TEMPLATE_TOOL_RESPONSE_CHINESE,
    GENERAL_AGENT_PROMPT
)
from kubechat.pipeline.base_pipeline import KUBE_CHAT_DOC_QA_REFERENCES, KUBE_CHAT_RELATED_QUESTIONS, Message, Pipeline
from kubechat.pipeline.keyword_extractor import IKExtractor
from kubechat.source.utils import async_run
from kubechat.utils.utils import (
    generate_fulltext_index_name,
    generate_qa_vector_db_collection_name,
    generate_vector_db_collection_name,
    now_unix_milliseconds,
)
from query.query import DocumentWithScore, get_packed_answer
from readers.base_embedding import get_embedding_model, rerank

logger = logging.getLogger(__name__)


class AgentPipeline(Pipeline):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.collection_id = self.collection.id
        collection_name = generate_vector_db_collection_name(self.collection_id)
        self.vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        self.vectordb_ctx["collection"] = collection_name

        config = json.loads(self.collection.config)
        self.embedding_model_name = config.get("embedding_model", settings.EMBEDDING_MODEL)
        self.embedding_model, self.vector_size = get_embedding_model(self.embedding_model_name)

        self.context_manager = ContextManager(collection_name, self.embedding_model, settings.VECTOR_DB_TYPE,
                                              self.vectordb_ctx)

        qa_collection_name = generate_qa_vector_db_collection_name(self.collection_id)
        self.qa_vectordb_ctx = json.loads(settings.VECTOR_DB_CONTEXT)
        self.qa_vectordb_ctx["collection"] = qa_collection_name
        self.qa_context_manager = ContextManager(qa_collection_name, self.embedding_model, settings.VECTOR_DB_TYPE,
                                                 self.qa_vectordb_ctx)

        # if not self.prompt_template:
            # self.prompt_template = DEFAULT_MODEL_MEMOTY_PROMPT_TEMPLATES.get(self.model,
            #                                                                  DEFAULT_CHINESE_PROMPT_TEMPLATE_V3)
        self.prompt = PromptTemplate(template=self.prompt_template, input_variables=["query", "context"])
        
        # agent
        self.bearer_token = config.get("bearer_token", "")
        self.tools = SeleceTools("https://api-dev.apecloud.cn", "./kubechat/agent/test.json",self.bearer_token)
        self.max_iterations = config.get("max_iterations", 3)
        


    async def new_ai_message(self, message, message_id, response, references):
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

    def parse(self, text: str):
        cleaned_output = text.strip()
        cleaned_output = text.replace("\n", "")
        try:
            response = parse_json_markdown(text)
            action_value = response.get("action", "")
            action_input_value = str(response.get("action_input", ""))
            if action_value == "Final Answer":
                return "Final Answer", action_input_value
            else:
                return action_value, action_input_value
        except:
            # 定义匹配正则
            action_pattern = r'"action"\s*:\s*"([^"]*)"'
            action_input_pattern = r'input"\s*:\s*\[([^\]]*)\]'
            # 提取出匹配到的action值
            action = re.search(action_pattern, cleaned_output)
            action_input = re.search(action_input_pattern, cleaned_output)
            if action:
                action_value = action.group(1)
            else:
                action_value = "Final Answer"
            if action_input:
                action_input_value = action_input.group(1)
            else:
                action_input_pattern = r'input"\s*:\s*"([^"]*)"'
                action_input = re.search(action_input_pattern, cleaned_output)
                action_input_value = action_input.group(1) if action_input else ""
            
            # 如果遇到'Final Answer'，则判断为本次提问的最终答案
            if action_value and action_input_value:
                return action_value, action_input_value
            else:
                return "Final Answer", ""
        
    async def agent(self, message, tot_history, tot_context):
        tool_names, tool_strings = self.tools.select(message)
        prompt = SUFFIX_CHINESE.format(tools=tool_strings, input=message) + FORMAT_INSTRUCTIONS_CHINESE.format(tool_names=tool_names)
        response = ""
        async for msg in self.predictor.agenerate_stream("", prompt, False):
            response += msg
            
        operate, answer = self.parse(response)
        history = ''
        known_info = ''
        
        iterations = 1
        while iterations < self.max_iterations and operate != "Final Answer":
            tool_response = self.tools.make_run(operate, answer)
            logger.info("\n[AI]:[%s]\n[TOOL]:%s\n", response, tool_response)
            if "输入有误" not in tool_response:
                known_info += tool_response + '\n'
            history += 'AI:{ai}\nHuman:{human}\n'.format(ai=str({"action": operate, "action_input": answer}), human=tool_response)
            
            # Determine whether tools need to be called
            # prompt = GENERAL_AGENT_PROMPT.format(input=message,tools=tool_strings,history = history)
            # response = ''
            # async for msg in self.predictor.agenerate_stream("", prompt, False):
            #     response += msg
            # logger.info("[check]:%s\n", response)
            
            # if "不" in response or "否" in response or 'no' in response:
            #     break
            
            # Determine which tools need to be called
            prompt = SUFFIX_CHINESE.format(tools=tool_strings, input=message) + TEMPLATE_TOOL_RESPONSE_CHINESE.format(history = history) + FORMAT_INSTRUCTIONS_CHINESE.format(tool_names=tool_names)
            response = ''
            async for msg in self.predictor.agenerate_stream("", prompt, False):
                response += msg
            operate, answer = self.parse(response)
            iterations += 1
        logger.info("\n[AI]:[%s]\n", response)
        
        prompt = QA_SELECT_PROMPT.format(input=message, known_info=known_info, answer=answer, context=tot_context)
        response = ''
        async for msg in self.predictor.agenerate_stream(tot_history, prompt, self.memory):
            response += msg
        return response
        
    async def run(self, message, gen_references=False, message_id=""):
        log_prefix = f"{message_id}|{message}"
        logger.info("[%s] start processing", log_prefix)

        references = []
        related_questions = []
        response = ""
        need_generate_answer = True
        need_related_question = True
        vector = self.embedding_model.embed_query(message)
        logger.info("[%s] embedding query end", log_prefix)
        # hyde_task = asyncio.create_task(self.generate_hyde_message(message))

        results = await async_run(self.qa_context_manager.query, message, score_threshold=0.5, topk=6, vector=vector)
        logger.info("[%s] find relevant qa pairs in vector db end", log_prefix)
        for result in results:
            result_text = json.loads(result.text)
            if result_text["answer"] != "" and result.score > 0.9:
                response = result_text["answer"]
            if result_text["question"] not in related_questions:
                related_questions.append(result_text["question"])
                
        if len(related_questions) >= 3:
            need_related_question = False
            
        if response != "":
            yield response
            
            if self.use_related_question and need_related_question:
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
            
            if self.bot_context != "":
                bot_context_result = DocumentWithScore(
                    text=self.bot_context,  # type: ignore
                    score=0,
                )
                results.append(bot_context_result)
                
            if len(results) > 1:
                results = await rerank(message, results)
                logger.info("[%s] rerank candidates end", log_prefix)
            else:
                logger.info("[%s] don't need to rerank ", log_prefix)

            candidates = results[:self.topk]

            if self.enable_keyword_recall:
                candidates = await self.filter_by_keywords(message, candidates)
                logger.info("[%s] filter keyword end", log_prefix)
            else:
                logger.info("[%s] no need to filter keyword", log_prefix)

            context = ""
            if len(candidates) > 0:
                # 500 is the estimated length of the prompt
                context = get_packed_answer(candidates, max(self.context_window - 500, 0))
            else:
                if self.oops != "":
                    response = self.oops
                    yield self.oops
                    need_generate_answer = False
                if self.welcome_question:
                    if len(self.welcome_question) >= 3:
                        related_questions = random.sample(self.welcome_question, 3)
                        need_related_question = False
                    else:
                        related_questions = self.welcome_question

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

                # prompt = self.prompt.format(query=message, context=context)
                # logger.info("[%s] final prompt is\n%s", log_prefix, prompt)

                response = await self.agent(message, history, context)
                yield response
                # await self.predictor.agenerate_stream(history, prompt, self.memory)
                # if operate != "Final Answer":
                #     async for msg in self.predictor.agenerate_stream(history, prompt, self.memory):
                #         yield msg
                #         response += msg

                for result in candidates:
                    # filter bot_context
                    if result.score == 0:
                        continue
                    references.append({
                        "score": result.score,
                        "text": result.text,
                        "metadata": result.metadata
                    })

        await self.add_human_message(message, message_id)
        logger.info("[%s] add human message end", log_prefix)

        await self.add_ai_message(message, message_id, response, references)
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

        if gen_references:
            yield KUBE_CHAT_DOC_QA_REFERENCES + json.dumps(references)
