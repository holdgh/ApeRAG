from elasticsearch import Elasticsearch
from typing import Optional
from base import Nosql
from llama_index.prompts.base import Prompt
import os
import json
import requests

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


class ElasticsearchClient(Nosql):
    def __init__(
            self,
            host,
            port,
            scheme: str = 'http',
            pwd: Optional[str] = None,
            prompt: Optional[Prompt] = _DEFAULT_PROMPT
    ):
        super().__init__(host, port, pwd, prompt)
        self.scheme = scheme

    def connect(self):
        self.conn = Elasticsearch([{'host': self.host, 'port': self.port, 'scheme': self.scheme}])

    def text_to_query(self, text):
        indices = self.conn.indices.get_alias(index="*")  # 获取所有索引
        documents = {}
        schema = ""
        for index in indices:
            response = self.conn.cat.indices(index=index, format="json")  # 获取索引的详细信息
            doc_count = response[0]['docs.count']  # 文档数量
            field_names = []
            if int(doc_count) > 0:
                mappings = self.conn.indices.get_mapping(index=index)  # 获取索引的映射信息
                field_names = list(mappings[index]['mappings'].keys())
            documents[index] = {
                'doc_count': doc_count,
                'fields': field_names
            }
            schema += "index: " + index + "\n"
            schema += "doc_count= " + doc_count + "\n"
            schema += "fields: "
            for field in field_names:
                schema += field + " "
            schema += "\n"
        print(schema)

        response_str, _ = self.llm_predict.predict(
            self.prompt,
            query_str=text,
            schema=schema,
        )
        return response_str

    def execute_query(self, query):
        lines = query.split('\n')
        # Get the method and path from the first line
        method, path = lines[1].split(' ')
        # Join the remaining lines and parse as JSON for the body
        body = json.loads(''.join(lines[2:]))
        # Construct the full URL
        url = f"{self.scheme}://{self.host}:{self.port}{path}"
        # Use the correct HTTP method
        if method.lower() == 'get':
            response = requests.get(url, json=body)
        elif method.lower() == 'post':
            response = requests.post(url, json=body)
        # Add more elif conditions here for other HTTP methods if needed
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")


if __name__ == "__main__":
    os.environ['OPENAI_API_KEY'] = "sk-xxx"
    es = ElasticsearchClient("localhost", 9200)
    es.connect()
    q = es.text_to_query("search for all docs in the index 'bank' ")
    print(q)
    # print(es.execute_query(q))
