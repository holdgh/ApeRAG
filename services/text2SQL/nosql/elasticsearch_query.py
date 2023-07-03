import json
import logging
from typing import Optional

import requests
from elasticsearch import Elasticsearch
from func_timeout import func_set_timeout
from langchain.llms.base import BaseLLM
from llama_index.prompts.base import Prompt

from services.text2SQL.base import DataBase

logger = logging.getLogger(__name__)

_ELASTICSEARCH_PROMPT_TPL = (
    "Given an input question, first create a syntactically correct Elasticsearch "
    "query to run, then look at the results of the query and return the answer."
    "You can order the results by a relevant column to return the most "
    "interesting examples in the database.\n"
    "Pay attention to use only the fields that you can see in the schema "
    "description. "
    "Be careful to not query for fields that do not exist. "
    "Use the following format:\n"
    "Question: Question here\n"
    "Query: Query to run\n"
    "Result: Result of the Query\n"
    "Answer: Final answer here\n"
    "Only use the fields with its type listed below.\n"
    "{schema}\n"
    "Question: {query_str}\n"
    "Query: "
)

_DEFAULT_PROMPT = Prompt(
    _ELASTICSEARCH_PROMPT_TPL,
    stop_token="\nResult:",
    prompt_type="text_to_sql",
)


class ElasticsearchClient(DataBase):
    def __init__(
        self,
        host,
        user: Optional[str] = None,
        pwd: Optional[str] = None,
        port: Optional[int] = None,
        scheme: Optional[str] = "http",
        prompt: Optional[Prompt] = _DEFAULT_PROMPT,
        llm: Optional[BaseLLM] = None,
        db_type: Optional[str] = "elasticsearch",
    ):
        if port is None:
            port = 9200
        super().__init__(host, port, user, pwd, prompt, db_type, llm)
        self.scheme = scheme

    def connect(
        self,
        verify: Optional[bool] = False,
        ca_cert: Optional[str] = None,
        client_key: Optional[str] = None,
        client_cert: Optional[str] = None,
    ) -> bool:
        kwargs = {
            "verify_certs": verify,
            "ca_certs": ca_cert,
            "client_key": client_key,
            "client_cert": client_cert,
        }

        @func_set_timeout(2)
        def ping():
            self.conn = Elasticsearch(
                [{"host": self.host, "port": self.port, "scheme": "https"}], **kwargs
            )
            return self.conn.ping()

        try:
            connected = ping()
        except BaseException as e:
            connected = False
            logger.warning("connect to elasticsearch failed, err={}".format(e))

        return connected

    def text_to_query(self, text):
        indices = self.conn.indices.get_alias(index="*")  # 获取所有索引
        documents = {}
        schema = ""
        for index in indices:
            response = self.conn.cat.indices(index=index, format="json")  # 获取索引的详细信息
            doc_count = response[0]["docs.count"]  # 文档数量
            field_names = []
            if int(doc_count) > 0:
                mappings = self.conn.indices.get_mapping(index=index)  # 获取索引的映射信息
                field_names = list(mappings[index]["mappings"].keys())
            documents[index] = {"doc_count": doc_count, "fields": field_names}
            schema += "index: " + index + "\n"
            schema += "doc_count= " + doc_count + "\n"
            schema += "fields: "
            for field in field_names:
                schema += field + " "
            schema += "\n"
        print(schema)

        generator, _ = self.llm_predict.stream(
            self.prompt,
            query_str=text,
            schema=schema,
        )
        return generator

    def execute_query(self, query):
        lines = query.split("\n")
        # Get the method and path from the first line
        method, path = lines[1].split(" ")
        # Join the remaining lines and parse as JSON for the body
        body = json.loads("".join(lines[2:]))
        # Construct the full URL
        url = f"{self.scheme}://{self.host}:{self.port}{path}"
        # Use the correct HTTP method
        if method.lower() == "get":
            response = requests.get(url, json=body)
        elif method.lower() == "post":
            response = requests.post(url, json=body)
        # Add more elif conditions here for other HTTP methods if needed
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        return response
