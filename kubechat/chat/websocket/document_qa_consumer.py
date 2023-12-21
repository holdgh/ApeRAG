import logging
from .base_consumer import BaseConsumer
from kubechat.pipeline.keyword_pipeline import KeywordPipeline

logger = logging.getLogger(__name__)


class DocumentQAConsumer(BaseConsumer):
    async def connect(self):
        await super().connect()
        self.pipeline = KeywordPipeline(bot=self.bot, collection=self.collection, history=self.history)
        self.use_default_token = self.pipeline.predictor.use_default_token

    async def predict(self, query, **kwargs):
        async for msg in self.pipeline.run(query, gen_references=True, **kwargs):
            yield msg
