from services.text2SQL.base import DataBase
from typing import Optional
from langchain.llms.base import BaseLLM
from llama_index import Prompt, LLMPredictor
from llama_index.prompts.default_prompts import DEFAULT_TEXT_TO_SQL_PROMPT


class Mysql(DataBase):
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
            port = 3306
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
            "ssl_ca": ca_cert,
            "ssl_cert": client_cert,
            "ssl_key": client_key,
        }

    def text_to_query(self, text):
        pass

    def execute_query(self, query):
        pass


