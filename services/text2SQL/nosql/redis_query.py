import logging
from func_timeout import func_set_timeout
from redis.client import Redis as RedisClient
from services.text2SQL.nosql.nosql import NoSQLBase
from llama_index.prompts.base import Prompt

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


class Redis(NoSQLBase):
    @func_set_timeout(2)
    def ping(self, verify, ca_cert, client_key, client_cert):
        if self.port is None:
            self.port = 6379
        self.conn = RedisClient(
            host=self.host,
            port=self.port,
            db=int(self.db) if self.db is not None else 0,
            ssl=verify,
            password=self.pwd,
            decode_responses=True,
            **self._get_ssl_args(ca_cert, client_key, client_cert),
        )
        return self.conn.ping()

    def _generate_schema(self):
        keys = self.conn.keys()
        return {k: self.conn.type(k) for k in keys}

    def execute_query(self, query):
        return self.conn.execute_command(query)

    def _get_ssl_args(self, ca_cert, client_key, client_cert):
        return {
            "ssl_ca_certs": ca_cert,
            "ssl_keyfile": client_key,
            "ssl_certfile": client_cert,
        }

    def _get_default_prompt(self):
        return Prompt(
            _REDIS_PROMPT_TPL,
            stop_token="\nResult:",
            prompt_type="text_to_sql",
        )