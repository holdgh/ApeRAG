import logging

from typing import Optional
from langchain.llms.base import BaseLLM
from llama_index import SQLDatabase, Prompt, LLMPredictor
from llama_index.prompts.default_prompts import DEFAULT_TEXT_TO_SQL_PROMPT
from sqlalchemy import create_engine, text
from services.text2SQL.base import DataBase
from abc import abstractmethod

logger = logging.getLogger(__name__)


class SQLBase(DataBase):
    def __init__(
            self,
            db_type,
            host,
            port,
            user: Optional[str] = "",
            pwd: Optional[str] = "",
            db: Optional[str] = "",
            prompt: Optional[Prompt] = DEFAULT_TEXT_TO_SQL_PROMPT,
            llm: Optional[BaseLLM] = None,
    ):
        super().__init__(host, port, user, pwd, prompt, db_type, llm)
        self.db = db

    @abstractmethod
    def _generate_db_url(self) -> str:
        pass

    @abstractmethod
    def _get_ssl_args(self, ca_cert, client_key, client_cert):
        pass

    def connect(
            self,
            verify: Optional[bool] = False,
            ca_cert: Optional[str] = None,
            client_key: Optional[str] = None,
            client_cert: Optional[str] = None,
            test_only: Optional[bool] = True,
    ) -> bool:
        try:
            self.conn = SQLDatabase(
                create_engine(
                    self._generate_db_url() +
                    self._get_ssl_args(ca_cert, client_key, client_cert)
                ),
                sample_rows_in_table_info=3,
                schema=self.db
            )
            with self.conn.engine.connect() as connection:
                _ = connection.execute(text("select 1"))
            if not test_only:
                self.schema = self.generate_sql_schema()
            return True
        except BaseException as e:
            print("Connect failed: err:{}".format(e))
            return False

    def text_to_query(self, query_str: str, sample_rows: Optional[int] = 3):
        llm_predictor = LLMPredictor(llm=self.llm)
        response, _ = llm_predictor.stream(
            prompt=self.prompt,
            query_str=query_str,
            schema=self.schema,
            dialect=self.db_type,
        )
        return response

    def generate_sql_schema(self) -> str:
        schema = ""
        usable_tables = self.conn.get_usable_table_names()
        for t in usable_tables:
            schema += self.conn.get_single_table_info(t) + "\n"
        return schema

    def execute_query(self, query):
        with self.conn.engine.connect() as connection:
            result = connection.execute(text(query))
        return result.all()
