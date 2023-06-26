import logging
import os
import sys
from typing import Optional, Required

from langchain.base_language import BaseLanguageModel
from langchain.chat_models import ChatOpenAI
from langchain.llms.base import LLM, BaseLLM
from llama_index.prompts.default_prompts import DEFAULT_TEXT_TO_SQL_TMPL
from llama_index.prompts.prompt_type import PromptType
from services.text2SQL.base import SQLDataBase
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import GPT4All, OpenAI
from llama_index import SQLStructStoreIndex, ServiceContext, Prompt, \
    LangchainEmbedding, LLMPredictor
from llama_index.indices.struct_store import SQLContextContainerBuilder
from sqlalchemy import create_engine
from utils.prompt import DefaultSQLPromptTemplate

local_llm_path = "/Users/alal/KubeChat/ggml-gpt4all-j-v1.3-groovy.bin"

os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"


# logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


class PostgreSQL:
    def __init__(self, user, pw,
                 database_name: str,
                 host: Optional[str] = "localhost", port: Optional[str] = "5432",
                 llm: Optional[BaseLLM] = None,
                 embed_model: Optional[LangchainEmbedding] = None,
                 prompt_text: Optional[str] = DEFAULT_TEXT_TO_SQL_TMPL):
        self.dialect = "postgresql"
        self.host = host
        self.port = port
        self.user = user
        self.pw = pw
        self.target_database = database_name
        self._self_check()
        self.engineUrl = f"{self.dialect}://{self.user}:{self.pw}@{self.host}/{self.target_database}"
        self.prompt_text = prompt_text
        self.db = None
        self.embed_model = None
        if llm is None:
            self.llm = GPT4All(model=local_llm_path, n_ctx=512)
        else:
            self.llm = llm
        if embed_model is None:
            self.embed_model = embed_model

    def _self_check(self):
        if not isinstance(self.user, str):
            raise TypeError("user must be a string")
        if not isinstance(self.pw, str):
            raise TypeError("password must be a string")
        if not isinstance(self.host, str):
            raise TypeError("host must be a string")
        if not isinstance(self.port, str):
            raise TypeError("port must be a string")
        if not isinstance(self.target_database, str):
            raise TypeError("database_name must be a string")

    def _connect(self):
        self.db = SQLDataBase(create_engine(self.engineUrl), sample_rows_in_table_info=0)

    def custom_prompt(self, prompt_text: str):
        self.prompt_text = prompt_text
        if not isinstance(self.prompt_text, str):
            raise TypeError("prompt_text must be a string")

    def custom_embedding(self, embed_model: Optional[LangchainEmbedding] = None):
        self.embed_model = embed_model

    def query(self, query_str: str, sample_rows: Optional[int] = 3) -> str:
        self._connect()
        prompt = Prompt(
            self.prompt_text,
            stop_token="\nSQLResult:",
            prompt_type=PromptType.TEXT_TO_SQL,
        )

        if isinstance(self.llm, LLM):
            # for local LLM
            sc = ServiceContext.from_defaults(llm=self.llm, embed_model=self.embed_model)
            context_builder = SQLContextContainerBuilder(sql_database=self.db,
                                                         context_str=self.db.generate_sql_context(sample_rows))
            # index
            index = SQLStructStoreIndex(
                service_context=sc,
                sql_database=self.db,
                sql_context_container=context_builder.build_context_container()
            )

            query_engine = index.as_query_engine(query_mode="nl", text_to_sql_prompt=prompt)
            response = query_engine.query(query_str)
            return response.extra_info["sql_query"]
        else:
            # for OpenAPI
            index = SQLStructStoreIndex(
                [],
                sql_database=self.db,
            )
            query_engine = index.as_query_engine(query_mode="nl", text_to_sql_prompt=prompt)
            response = query_engine.query(query_str)
            return response.extra_info["sql_query"]


if __name__ == '__main__':
    openAI = OpenAI()
    pg = PostgreSQL(user="postgres", pw="", database_name="postgres",llm=OpenAI)
    response = pg.query("how old is Mary?")
    # print(response, len(response))
