import logging
import sys

from typing import Optional
from langchain import OpenAI
from langchain.llms import GPT4All
from llama_index import LangchainEmbedding, SQLDatabase, Prompt, LLMPredictor
from llama_index.prompts.default_prompts import DEFAULT_TEXT_TO_SQL_TMPL
from llama_index.prompts.prompt_type import PromptType
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)
local_llm_path = "/Users/alal/KubeChat/ggml-gpt4all-j-v1.3-groovy.bin"
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

Dialect = ["mysql", "postgresql", "sqlite", "oracle", "mssql"]
Driver = {"mysql":"+pymysql","postgresql":""}

class SQLBase:
    def __init__(self, user, pw,
                 database_name: str,
                 host: Optional[str] = "localhost",
                 port: Optional[str] = None,
                 dialect: Optional[str] = "mysql",
                 islocal: Optional[bool] = False,
                 embed_model: Optional[LangchainEmbedding] = None,
                 prompt_text: Optional[str] = DEFAULT_TEXT_TO_SQL_TMPL):
        self.dialect = dialect
        self.user = user
        self.pw = pw
        self.target_database = database_name
        self.host = host
        self.port = port
        self._self_check()
        self.engineUrl = self._generate_db_url()
        self.prompt_text = prompt_text
        self.db = None

        self.embed_model = None
        self.islocal = False
        if islocal is True:
            self.islocal = True
            self.llm = GPT4All(model=local_llm_path, n_ctx=512)
        else:
            self.llm = OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=-1)
        if embed_model is not None:
            self.embed_model = embed_model

    def _generate_db_url(self) -> str:
        if self.port is not None:
            return f"{self.dialect}{Driver[self.dialect]}://{self.user}:{self.pw}@{self.host}:{self.port}/{self.target_database}"
        else:
            return f"{self.dialect}{Driver[self.dialect]}://{self.user}:{self.pw}@{self.host}/{self.target_database}"

    def _self_check(self):
        if not isinstance(self.user, str):
            raise TypeError("user must be a string")
        if not isinstance(self.pw, str):
            raise TypeError("password must be a string")
        if not isinstance(self.host, str):
            raise TypeError("host must be a string")
        if self.port is not None and isinstance(self.port, str):
            raise TypeError("port must be a string")
        if not isinstance(self.target_database, str):
            raise TypeError("database_name must be a string")
        if not isinstance(self.dialect, str):
            raise TypeError("database_name must be a string")

    def _connect(self):
        self.db = SQLDatabase(create_engine(self.engineUrl), sample_rows_in_table_info=0)

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
        # schema
        schema = self.generate_sql_schema(sample_rows)
        llm_predictor = LLMPredictor(llm=self.llm)
        logger.info(f"> prompt format: {prompt.format(schema=schema, dialect=self.dialect, query_str=query_str)}")
        response, _ = llm_predictor.predict(prompt=prompt, query_str=query_str, schema=schema,
                                            dialect=self.dialect)
        return response

    def generate_sql_schema(self, sample_rows: int) -> str:
        """
        generate the schema info from db
        :param sample_rows: the rows number sample from the table
        :return: schema
        """
        scheme = self.db.get_table_info_no_throw()
        tables = self.db.get_usable_table_names()
        if sample_rows != 0:
            self.db._sample_rows_in_table_info = sample_rows
            scheme.lstrip('\n')
            meta_tables = [
                tbl
                for tbl in self.db._metadata.sorted_tables
                if tbl.name in set(tables)
                   and not (self.dialect == "sqlite" and tbl.name.startswith("sqlite_"))
            ]
            for table in meta_tables:
                scheme += f"\nhere are some example rows data in table \"{table}\" to help you understand the table struct:" + f"\n{self.db._get_sample_rows(table)}\n"
        # more database info could add here

        return scheme
