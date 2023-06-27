from pymongo import MongoClient
from typing import Optional
from services.text2SQL.nosql.base import Nosql
from llama_index.prompts.base import Prompt

_MONGODB_PROMPT_TPL = (
    "You are now an expert on mongodb，Given an input question, first create a syntactically correct MONGODB "
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
    _MONGODB_PROMPT_TPL,
    stop_token="\nResult:",
    prompt_type="text_to_sql",
)


class Mongo(Nosql):
    def __init__(
            self,
            host,
            port,
            collection,
            pwd: Optional[str] = None,
            db: Optional[str] = '',
            prompt: Optional[Prompt] = _DEFAULT_PROMPT
    ):
        super().__init__(host, port, pwd, prompt)
        self.db = db
        self.collection = collection

    def connect(self, ssl_enable=False, ssl_ca_certs='', ssl_certfile='', ssl_keyfile=''):
        if ssl_enable:
            ssl_options = {
                'ssl': True,
                'ssl_ca_certs': ssl_ca_certs,  # CA证书路径
                'ssl_certfile': ssl_certfile,  # 客户端SSL证书路径
                'ssl_keyfile': ssl_keyfile,  # 客户端私钥路径
                # 其他可选参数
            }
            try:
                self.conn = MongoClient("mongodb://" + self.host + ':' + self.port, **ssl_options)
                return True
            except Exception as e:
                print("Failed to connect to MongoDB:", str(e))
                return False
        else:
            try:
                self.conn = MongoClient("mongodb://" + self.host + ':' + self.port)
                return True
            except Exception as e:
                print("Failed to connect to MongoDB:", str(e))
                return False

    def text_to_query(self, text):
        # Connect to the MongoDB database and collection
        connect = self.conn[str(self.db)][str(self.collection)]
        document = connect.find_one()

        # Print key and data type to schema
        schema = 'Collection: ' + self.collection + '\n'
        for key in document.keys():
            data_type = type(document[key])
            schema += f"Key: {key}, Data Type: {data_type}\n"

        # Call the llm_predict.predict() method with the appropriate parameters
        response_str, _ = self.llm_predict.predict(
            Prompt(
                _MONGODB_PROMPT_TPL,
                stop_token="\nResult:",
                prompt_type="text_to_sql",
            ),
            query_str=text,
            schema=schema,
        )

        return response_str

    # pymongo does not support a way to directly execute js query statements
    def execute_query(self, query):
        return
