import json
from .base_consumer import BaseConsumer
from kubechat.utils.db import query_collection, new_db_client


class Text2SQLConsumer(BaseConsumer):
    def connect(self):
        super().connect()
        collection = query_collection(self.user, self.collection_id)
        config = json.loads(collection.config)
        self.client = new_db_client(config)
        if not self.client.connect(
            False,
        ):
            raise Exception("can not connect to db")

    def predict(self, query):
        response = self.client.text_to_query(query)
        for tokens in response.iter_content():
            yield tokens.decode("ascii")



