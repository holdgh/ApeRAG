import logging

from .base_consumer import BaseConsumer
from ..pipeline.pipeline import KeywordPipeline

logger = logging.getLogger(__name__)


class DocumentQAConsumer(BaseConsumer):
    async def predict(self, query, **kwargs):
        async for msg in self.pipeline.run(query, gen_references=True, **kwargs):
            yield msg
