# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from aperag.pipeline.fake_pipeline import FakePipeline

from .base_consumer import BaseConsumer

logger = logging.getLogger(__name__)


class FakeConsumer(BaseConsumer):
    async def predict(self, query, **kwargs):
        pipeline = FakePipeline(bot=self.bot, collection=self.collection, history=self.history)
        async for msg in pipeline.run(query, gen_references=True, **kwargs):
            yield msg
