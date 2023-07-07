import logging
from abc import abstractmethod
from typing import Optional

from langchain.llms.base import BaseLLM
from llama_index import Prompt, SQLDatabase
from llama_index.prompts.default_prompts import DEFAULT_TEXT_TO_SQL_PROMPT
from sqlalchemy import create_engine, text

from services.text2SQL.base import DataBase

logger = logging.getLogger(__name__)


class SQLBase(DataBase):
    def __init__(
        self,
        db_type,
        host,
        port: Optional[int] = None,
        user: Optional[str] = "",
        pwd: Optional[str] = "",
        db: Optional[str] = "",
        prompt: Optional[Prompt] = None,
        llm: Optional[BaseLLM] = None,
    ):
        super().__init__(host, port, user, pwd, prompt, db_type, llm)
        self.db = db

    @abstractmethod
    def _generate_db_url(self) -> str:
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
                    self._generate_db_url(),
                    connect_args=self._get_ssl_args(verify, ca_cert, client_key, client_cert),
                ),
                sample_rows_in_table_info=3,
                schema=self.db,
            )
            with self.conn.engine.connect() as connection:
                _ = connection.execute(text("select 1"))
            if not test_only:
                self.schema = self._generate_schema()
            return True
        except BaseException as e:
            print("Connect failed: err:{}".format(e))
            return False

    def text_to_query(self, query_str: str, sample_rows: Optional[int] = 3):
        if self.prompt is None:
            self.prompt = DEFAULT_TEXT_TO_SQL_PROMPT
        response, _ = self.llm_predict.stream(
            prompt=self.prompt,
            query_str=query_str,
            schema=self.schema,
            dialect=self.db_type,
        )
        return response

    def _generate_schema(self) -> str:
        schema = ""
        usable_tables = self.conn.get_usable_table_names()
        for t in usable_tables:
            schema += self.conn.get_single_table_info(t) + "\n"
        return schema

    def execute_query(self, query):
        response = []
        try:
            with self.conn.engine.connect() as connection:
                result = connection.execute(text(query))
            keys = list(result.keys())
            for row in result.all():
                temp_dict = {}
                for i in range(len(keys)):
                    temp_dict[keys[i]] = row[i]
                response.append(temp_dict)
        except BaseException as e:
            response = {"error": e}

        return response

    @abstractmethod
    def get_database_list(self):
        pass
