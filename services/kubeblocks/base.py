from abc import ABC, abstractmethod
from typing import Optional

from langchain import OpenAI
from langchain.llms.base import BaseLLM
from llama_index import Prompt
from llama_index.langchain_helpers.chain_wrapper import LLMPredictor


class KubeBlocks(ABC):
    def __init__(
            self,
            chat_type: str,
            llm: Optional[BaseLLM] = None,
    ):
        self.chat_type = chat_type
        if llm is None:
            self.llm = OpenAI(
                temperature=0,
                model_name="text-davinci-003",
                max_tokens=-1,
                streaming=True,
            )
        else:
            self.llm = llm
        self.llm_predict = LLMPredictor(llm=self.llm)

    @abstractmethod
    def predict(self, text: str):
        pass
