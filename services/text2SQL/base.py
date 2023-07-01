from llama_index.langchain_helpers.chain_wrapper import LLMPredictor
from abc import abstractmethod
from typing import Optional
from llama_index import Prompt
from langchain.llms.base import BaseLLM
from abc import ABC
from langchain import OpenAI


class DataBase(ABC):
    def __init__(
            self,
            host: str,
            port: int,
            user: str,
            pwd: str,
            prompt: Prompt,
            db_type: str,
            llm: Optional[BaseLLM] = None,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.db_type = db_type
        self.conn = None
        self.prompt = prompt

        if llm is None:
            self.llm = OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=-1, streaming=True)
        else:
            self.llm = llm
        self.llm_predict = LLMPredictor(llm=self.llm)

    @abstractmethod
    def connect(
            self,
            verify: Optional[bool] = False,
            ca_cert: Optional[str] = None,
            client_key: Optional[str] = None,
            client_cert: Optional[str] = None,
    ) -> bool:
        pass

    @abstractmethod
    def text_to_query(self, text):
        pass

    @abstractmethod
    def execute_query(self, query):
        pass
