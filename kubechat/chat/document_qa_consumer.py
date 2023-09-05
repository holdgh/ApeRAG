import logging

from .base_consumer import BaseConsumer
from ..pipeline.pipeline import QueryRewritePipeline

logger = logging.getLogger(__name__)


class DocumentQAConsumer(BaseConsumer):
    async def predict(self, query, **kwargs):
        pipeline = QueryRewritePipeline(bot=self.bot, collection=self.collection, history=self.history)
        async for msg in pipeline.run(query, gen_references=True, **kwargs):
            yield msg
