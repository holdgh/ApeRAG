from langchain import OpenAI
from llama_index.langchain_helpers.chain_wrapper import LLMPredictor
from abc import abstractmethod


class Nosql:
    def __init__(self, host, port, pwd, prompt):
        self.host = host
        self.port = port
        self.pwd = pwd
        self.llm = OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=-1)
        self.llm_predict = LLMPredictor(llm=self.llm)
        self.conn = None
        self.prompt = prompt

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def text_to_query(self, text):
        pass

    @abstractmethod
    def execute_query(self, query):
        pass
