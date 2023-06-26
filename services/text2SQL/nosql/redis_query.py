from redis.client import Redis as RedisClient
from typing import Optional
from services.text2SQL.nosql.base import Nosql
from llama_index.prompts.base import Prompt

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


class Redis(Nosql):
    def __init__(
        self,
        host,
        port,
        pwd: Optional[str] = None,
        db: Optional[int] = 0,
        prompt: Optional[Prompt] = _DEFAULT_PROMPT
    ):
        super().__init__(host, port, pwd, prompt)
        self.db = db

    def connect(self):
        self.conn = RedisClient(host=self.host, port=self.port, db=self.db, password=self.pwd, decode_responses=True)

    def text_to_query(self, text):
        keys = self.conn.keys()
        schema = {k: self.conn.type(k) for k in keys}
        print(schema)

        response_str, _ = self.llm_predict.predict(
            self.prompt,
            query_str=text,
            schema=schema,
        )
        return response_str

    def execute_query(self, query):
        return self.conn.execute_command(query)

