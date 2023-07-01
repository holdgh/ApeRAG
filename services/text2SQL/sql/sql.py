import logging

from typing import Optional, Dict
from langchain.llms.base import BaseLLM
from llama_index import SQLDatabase, Prompt, LLMPredictor
from llama_index.prompts.default_prompts import DEFAULT_TEXT_TO_SQL_PROMPT
from sqlalchemy import create_engine, text
from services.text2SQL.base import DataBase

logger = logging.getLogger(__name__)

DEFAULT_PORT: Dict[str, int] = {
    "mysql": 3306,
    "postgresql": 5432,
    "sqlite": None,
    "oracle": 1521,
}

DEFAULT_DRIVER: Dict[str, str] = {
    "mysql": "pymysql",
    "postgresql": "psycopg2",
}


class SQLBase(DataBase):
    def __init__(
            self,
            db_type,
            host,
            user: Optional[str] = "",
            pwd: Optional[str] = "",
            db: Optional[str] = "",
            port: Optional[int] = None,
            prompt: Optional[Prompt] = DEFAULT_TEXT_TO_SQL_PROMPT,
            llm: Optional[BaseLLM] = None,
    ):
        if port is None:
            port = DEFAULT_PORT[db_type]
        super().__init__(host, port, user, pwd, prompt, db_type, llm)
        self.db = db
        self.conn = None
        self.schema = None

    def _generate_db_url(self) -> str:
        return f"{self.db_type}+{DEFAULT_DRIVER[self.db_type]}://{self.user}:{self.pwd}@{self.host}:{self.port}/{self.db}"

    def _get_ssl_args(self, ca_cert, client_key, client_cert):
        args = {}
        if self.db_type == "mysql":
            args["ssl_ca"] = ca_cert
            args["ssl_cert"] = client_cert
            args["ssl_key"] = client_key
        return args

    def connect(
            self,
            verify: Optional[bool] = False,
            ca_cert: Optional[str] = None,
            client_key: Optional[str] = None,
            client_cert: Optional[str] = None,
    ) -> bool:
        kwargs = self._get_ssl_args(ca_cert, client_key, client_cert) if verify else {}
        try:
            self.conn = SQLDatabase(create_engine(self._generate_db_url(), **kwargs), sample_rows_in_table_info=3)
            with self.conn.engine.connect() as connection:
                _ = connection.execute(text("select 1"))
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
        schema = self.conn.get_table_info_no_throw(["user"])
        # print("get schema:{} finish".format(schema))
        return schema

    def execute_query(self, query):
        with self.conn.engine.connect() as connection:
            result = connection.execute(query)
        return result

    def get_database_list(self):
        cmd = ""
        match self.db_type:
            case "mysql":
                cmd = "show databases;"
            case "postgresql":
                cmd = "select datname from pg_database;"

        db_list = []
        with self.conn.engine.connect() as connection:
            db_all = connection.execute(text(cmd))
            for db in db_all:
                db_list.append(db[0])
        return db_list
