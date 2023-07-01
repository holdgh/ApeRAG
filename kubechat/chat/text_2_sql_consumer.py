import json
from .base_consumer import BaseConsumer
from kubechat.utils.db import query_collection, new_db_client
from kubechat.utils.utils import extract_database_and_execute


class Text2SQLConsumer(BaseConsumer):
    def connect(self):
        super().connect()
        collection = query_collection(self.user, self.collection_id)
        database, execute = extract_database_and_execute(self.scope["query_string"].decode())
        config = json.loads(collection.config)
        config["db_name"] = database

        self.client = new_db_client(config)
        if not self.client.connect(
            False,
            test_only=False
        ):
            raise Exception("can not connect to db")

    def predict(self, query):
        response = self.client.text_to_query(query)
        for tokens in response:
            yield tokens



