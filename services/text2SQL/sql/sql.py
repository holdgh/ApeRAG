import logging

from typing import Optional, Dict
from langchain.llms.base import BaseLLM
from llama_index import LangchainEmbedding, Prompt, LLMPredictor
from llama_index.prompts.default_prompts import DEFAULT_TEXT_TO_SQL_PROMPT
from sqlalchemy import create_engine, text
from services.text2SQL.base import DataBase
from common.sql_database import Database as SQLDatabase

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
            embed_model: Optional[LangchainEmbedding] = None,
            prompt: Optional[Prompt] = DEFAULT_TEXT_TO_SQL_PROMPT,
            llm: Optional[BaseLLM] = None,
    ):
        if port is None:
            port = DEFAULT_PORT[db_type]
        super().__init__(host, port, user, pwd, prompt, db_type, llm)
        self.engineUrl = self._generate_db_url()
        self.db = db
        self.conn = None
        self.embed_model = embed_model if embed_model is not None else None

    def _generate_db_url(self) -> str:
        return f"{self.db_type}+{DEFAULT_DRIVER[self.db_type]}://{self.user}:{self.pwd}@{self.host}:{self.port}"

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
            self.conn = SQLDatabase(create_engine(self.engineUrl, **kwargs))
            with self.conn.engine.connect() as connection:
                _ = connection.execute(text("select 1"))
                return True
        except BaseException as e:
            print("Connect failed: err:{}".format(e))
            return False

    def text_to_query(self, query_str: str, sample_rows: Optional[int] = 3) -> str:
        schema = self.generate_sql_schema(sample_rows)
        llm_predictor = LLMPredictor(llm=self.llm)
        response, _ = llm_predictor.predict(
            prompt=self.prompt,
            query_str=query_str,
            schema=schema,
            dialect=self.db_type
        )
        return response.strip()

    def generate_sql_schema(self, sample_rows: int) -> str:
        """
        generate the schema info from db
        :param sample_rows: the rows number sample from the table
        :return: schema
        """
        schema = self.conn.get_table_info_no_throw()
        tables = self.conn.get_usable_table_names()
        if sample_rows != 0:
            self.db._sample_rows_in_table_info = sample_rows
            schema.lstrip('\n')
            meta_tables = [
                tbl
                for tbl in self.conn._metadata.sorted_tables
                if tbl.name in set(tables)
                   and not (self.db_type == "sqlite" and tbl.name.startswith("sqlite_"))
            ]
            for table in meta_tables:
                schema += f"\nhere are some example rows data in table \"{table}\" " \
                          f"to help you understand the table struct:" + f"\n{self.conn._get_sample_rows(table)}\n"
        # more database info could add here

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
