import logging
from services.text2SQL.base import DataBase
from typing import Optional
from llama_index import Prompt
from langchain.llms.base import BaseLLM
from abc import abstractmethod

logger = logging.getLogger(__name__)


class NoSQLBase(DataBase):
    def __init__(
            self,
            db_type,
            host,
            port,
            user: Optional[str] = "",
            pwd: Optional[str] = "",
            db: Optional[str] = "",
            prompt: Optional[Prompt] = None,
            llm: Optional[BaseLLM] = None,
    ):
        super().__init__(host, port, user, pwd, prompt, db_type, llm)
        self.db = db

    @abstractmethod
    def ping(self, verify, ca_cert, client_key, client_cert):
        pass

    def connect(
            self,
            verify: Optional[bool] = False,
            ca_cert: Optional[str] = None,
            client_key: Optional[str] = None,
            client_cert: Optional[str] = None,
            test_only: Optional[bool] = True,
    ):
        try:
            connected = self.ping(verify, ca_cert, client_key, client_cert)
            if not test_only:
                self.schema = self._generate_schema()
        except BaseException as e:
            connected = False
            logger.warning("connect to redis failed, err={}".format(e))

        return connected

    @abstractmethod
    def _get_default_prompt(self):
        pass

    def text_to_query(self, text):
        if self.prompt is None:
            self.prompt = self._get_default_prompt()
        generator, _ = self.llm_predict.stream(
            prompt=self.prompt,
            query_str=text,
            schema=self.schema,
        )
        return generator
