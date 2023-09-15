import logging

from .base_consumer import BaseConsumer
from ..pipeline.pipeline import QueryRewritePipeline, KeywordPipeline

logger = logging.getLogger(__name__)


class DocumentQAConsumer(BaseConsumer):
    async def predict(self, query, **kwargs):
        pipeline = KeywordPipeline(bot=self.bot, collection=self.collection, history=self.history)
        async for msg in pipeline.run(query, gen_references=True, **kwargs):
            yield msg
