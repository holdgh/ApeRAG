import logging
from func_timeout import func_set_timeout
from pymongo import MongoClient
from typing import Optional
from services.text2SQL.base import DataBase
from llama_index.prompts.base import Prompt
from langchain.llms.base import BaseLLM

logger = logging.getLogger(__name__)

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


class Mongo(DataBase):
    def __init__(
            self,
            host,
            user: Optional[str] = None,
            pwd: Optional[str] = "",
            port: Optional[int] = 27017,
            db: Optional[str] = None,
            collection: Optional[str] = None,
            prompt: Optional[Prompt] = _DEFAULT_PROMPT,
            llm: Optional[BaseLLM] = None,
    ):
        super().__init__(host, port, user, pwd, prompt, "mongo", llm)
        self.db = db
        self.collection = collection

    def connect(
            self,
            verify: Optional[bool] = False,
            ca_cert: Optional[str] = None,
            client_key: Optional[str] = None,
            client_cert: Optional[str] = None
    ):
        kwargs = {
            'directConnection': True,
            'ssl': verify,
            "tlsCAFile": ca_cert,
            "tlsCertificateKeyFile": client_key,
        }

        @func_set_timeout(2)
        def ping():
            if self.user is not None:
                self.conn = MongoClient("mongodb://" + self.user + ':' + self.pwd +
                                        '@' + self.host + ':' + str(self.port), **kwargs)
            else:
                self.conn = MongoClient("mongodb://" + self.host + ':' + str(self.port), **kwargs)
            return self.conn.admin.command("ping")

        try:
            connected = ping()
        except BaseException as e:
            connected = False
            logger.warning("connect to mongo failed, err={}".format(e))

        return connected

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
