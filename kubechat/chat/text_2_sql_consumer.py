import json
from .base_consumer import BaseConsumer
from kubechat.utils.db import query_collection, new_db_client
from kubechat.utils.utils import extract_database_and_execute
from typing import Generator


class Text2SQLConsumer(BaseConsumer):
    def connect(self):
        super().connect()
        collection = query_collection(self.user, self.collection_id)
        config = json.loads(collection.config)
        database, execute_at_once = extract_database_and_execute(self.scope["query_string"].decode(), config["db_type"])

        if database is not None:
            config["db_name"] = database

        self.client = new_db_client(config)
        self.execute_at_once = execute_at_once
        if not self.client.connect(
            False,
            test_only=False
        ):
            raise Exception("can not connect to db")

    def predict(self, query):
        if self.msg_type == "sql":
            response = self.client.execute_query(query)
        else:
            if self.execute_at_once == "true":
                sql_iter = self.client.text_to_query(query)
                sql = ""
                for tokens in sql_iter:
                    sql += tokens
                response = self.client.execute_query(sql)
            else:
                self.response_type = "sql"
                response = self.client.text_to_query(query)

        if isinstance(response, Generator):
            for tokens in response:
                yield str(tokens)
        else:
            for tokens in response:
                yield str(tokens) + "\n"

