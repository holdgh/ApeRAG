import logging
import traceback
from func_timeout import func_set_timeout
import clickhouse_connect
from typing import Optional
from services.text2SQL.base import DataBase
from llama_index.prompts.base import Prompt
from langchain.llms.base import BaseLLM

logger = logging.getLogger(__name__)

_CLICKHOUSE_PROMPT_TPL = (
    "Given an input question, first create a syntactically correct clickhouse "
    "query to run, then look at the results of the query and return the answer."
    "You can order the results by a relevant column to return the most "
    "interesting examples in the database.\n"
    "Pay attention to use only the columns that you can see in the schema "
    "description. "
    "Be careful to not query for columns that do not exist. "
    "Use the following format:\n"
    "Question: Question here\n"
    "Query: Query to run\n"
    "Result: Result of the Query\n"
    "Answer: Final answer here\n"
    "Only use the columns with its type listed below.\n"
    "{schema}\n"
    "Question: {query_str}\n"
    "Query: "
)

_DEFAULT_PROMPT = Prompt(
    _CLICKHOUSE_PROMPT_TPL,
    stop_token="\nResult:",
    prompt_type="text_to_sql",
)


class Clickhouse(DataBase):
    def __init__(
        self,
        host,
        user: Optional[str] = "default",
        pwd: Optional[str] = None,
        port: Optional[int] = 8123,
        db: Optional[str] = None,
        prompt: Optional[Prompt] = _DEFAULT_PROMPT,
        llm: Optional[BaseLLM] = None,
    ):
        super().__init__(host, port, user, pwd, prompt, "clickhouse", llm)
        self.user = user
        self.db = db

    def connect(
            self,
            verify: Optional[bool] = False,
            ca_cert: Optional[str] = None,
            client_key: Optional[str] = None,
            client_cert: Optional[str] = None,
    ):
        kwargs = {
            "verify": verify,
            "ca_cert": ca_cert,
            "client_cert_key": client_key,
            "client_cert": client_cert,
        }

        @func_set_timeout(2)
        def ping():
            self.conn = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                database=self.db,
                username=self.user,
                password=self.pwd,
                **kwargs
            )
            return self.conn.ping()

        try:
            connected = ping()
        except Exception as e:
            connected = False
            logger.warning("connect to clickhouse failed, err={}".format(e))

        return connected

    # get the schemas of all tables in the database
    # and do query
    def text_to_query(self, text):
        tables = self.conn.command("show tables")
        tables = tables.splitlines()
        schema = ""
        i = 1
        for line in tables:
            tableschema = self.conn.command("show create table " + line)
            schema += "the create table statements of table " + str(i) + " is "
            schema += tableschema
            schema += "\n"
            i += 1

        response_str, _ = self.llm_predict.predict(
            self.prompt,
            query_str=text,
            schema=schema,
        )
        return response_str

    def execute_query(self, query):
        return self.conn.command(query)
