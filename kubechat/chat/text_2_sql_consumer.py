import json
from typing import Generator

from sqlalchemy import Row

from kubechat.utils.db import new_db_client, query_collection
from kubechat.utils.utils import extract_database

from .base_consumer import BaseConsumer


class Text2SQLConsumer(BaseConsumer):
    async def connect(self):
        await super().connect()
        collection = await query_collection(self.user, self.collection_id)
        config = json.loads(collection.config)
        database = extract_database(
            self.scope["query_string"].decode(), config["db_type"]
        )

        if database is not None:
            config["db_name"] = database

        self.client = new_db_client(config)
        if not self.client.connect(False, test_only=False):
            raise Exception("can not connect to db")

    async def predict(self, query, **kwargs):
        if self.msg_type == "sql":
            response = self.client.execute_query(query)
        else:
            self.response_type = "sql"
            response = self.client.text_to_query(query)

        if hasattr(response, "__iter__"):
            if self.msg_type == "sql":
                yield json.dumps(response)
            else:
                for tokens in response:
                    yield str(tokens)
        else:
            yield str(response)
