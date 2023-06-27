import clickhouse_connect
from typing import Optional
from services.text2SQL.nosql.base import Nosql
from llama_index.prompts.base import Prompt

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


class Clickhouse(Nosql):
    def __init__(
        self,
        host,
        port,
        username: Optional[str] = "default",
        pwd: Optional[str] = "",
        db: Optional[str] = None,
        prompt: Optional[Prompt] = _DEFAULT_PROMPT,
    ):
        super().__init__(host, port, pwd, prompt)
        self.username = username
        self.db = db

    def connect(self):
        self.conn = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            database=self.db,
            username=self.username,
            password=self.pwd,
        )

    # get the schemas of all tables in the database
    # and do query
    def text_to_query(self, text):
        tables = self.conn.command("show tables")
        print(tables)
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
