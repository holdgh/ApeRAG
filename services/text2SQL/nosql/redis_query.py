import logging
from func_timeout import func_set_timeout
from redis.client import Redis as RedisClient
from typing import Optional
from services.text2SQL.base import DataBase
from llama_index.prompts.base import Prompt
from langchain.llms.base import BaseLLM

logger = logging.getLogger(__name__)

_REDIS_PROMPT_TPL = (
    "Given an input question, first create a syntactically correct redis "
    "query to run, then look at the results of the query and return the answer."
    "You can order the results by a relevant column to return the most "
    "interesting examples in the database.\n"
    "Pay attention to use only the keys that you can see in the schema "
    "description. "
    "Be careful to not query for keys that do not exist. "
    "Use the following format:\n"
    "Question: Question here\n"
    "Query: Query to run\n"
    "Result: Result of the Query\n"
    "Answer: Final answer here\n"
    "Only use the keys with its type listed below.\n"
    "{schema}\n"
    "Question: {query_str}\n"
    "Query: "
)

_DEFAULT_PROMPT = Prompt(
    _REDIS_PROMPT_TPL,
    stop_token="\nResult:",
    prompt_type="text_to_sql",
)


class Redis(DataBase):
    def __init__(
            self,
            host,
            user: Optional[str] = None,
            pwd: Optional[str] = None,
            port: Optional[int] = None,
            db: Optional[int] = 0,
            prompt: Optional[Prompt] = _DEFAULT_PROMPT,
            llm: Optional[BaseLLM] = None,
            db_type: Optional[str] = "redis",
    ):
        if port is None:
            port = 6379
        super().__init__(host, port, user, pwd, prompt, db_type, llm)
        self.db = db

    def connect(
            self,
            verify: Optional[bool] = False,
            ca_cert: Optional[str] = None,
            client_key: Optional[str] = None,
            client_cert: Optional[str] = None,
    ):
        kwargs = {
            "ssl_ca_certs": ca_cert,
            "ssl_keyfile": client_key,
            "ssl_certfile": client_cert,
        }

        @func_set_timeout(2)
        def ping():
            self.conn = RedisClient(
                host=self.host,
                port=self.port,
                db=self.db,
                ssl=verify,
                password=self.pwd,
                decode_responses=True,
                **kwargs,
            )
            return self.conn.ping()

        try:
            connected = ping()
        except BaseException as e:
            connected = False
            logger.warning("connect to redis failed, err={}".format(e))

        return connected

    def text_to_query(self, text):
        keys = self.conn.keys()
        schema = {k: self.conn.type(k) for k in keys}

        response_str, _ = self.llm_predict.predict(
            self.prompt,
            query_str=text,
            schema=schema,
        )
        return response_str.strip()

    def execute_query(self, query):
        return self.conn.execute_command(query)
