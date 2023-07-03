import json
from typing import Generator

from sqlalchemy import Row

from kubechat.utils.db import new_db_client, query_collection
from kubechat.utils.utils import extract_database_and_execute

from .base_consumer import BaseConsumer


class Text2SQLConsumer(BaseConsumer):
    def connect(self):
        super().connect()
        collection = query_collection(self.user, self.collection_id)
        config = json.loads(collection.config)
        database, execute_at_once = extract_database_and_execute(
            self.scope["query_string"].decode(), config["db_type"]
        )

        if database is not None:
            config["db_name"] = database

        self.client = new_db_client(config)
        self.execute_at_once = execute_at_once
        if not self.client.connect(False, test_only=False):
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
            # TODO: temporarily format
            if not hasattr(response, "__iter__"):
                yield "true" if response > 0 else "false"
            for tokens in response:
                if isinstance(tokens, Row):
                    t = ""
                    for i in dict(tokens._mapping):
                        t += str(i) + ":" + str(dict(tokens._mapping)[i]) + " "
                    tokens = t
                yield str(tokens) + "\n"
