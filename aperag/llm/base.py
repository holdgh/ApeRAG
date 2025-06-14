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
from abc import ABC, abstractmethod

from aperag.llm.completion_service import CompletionService

logger = logging.getLogger(__name__)


class LLMConfigError(Exception):
    """
    LLMConfigError is raised when the LLM config is invalid.
    """


class LLMAPIError(Exception):
    """
    LLMAPIError is raised when error occurs when calling LLM API.
    """


# TODO: remove Predictor, just use CompletionService
class Predictor(ABC):
    def __init__(self, **kwargs):
        self.max_tokens = kwargs.get("max_tokens", 4096)
        self.temperature = kwargs.get("temperature", 0.1)

    @abstractmethod
    async def agenerate_stream(self, history, prompt, memory):
        pass

    @abstractmethod
    def generate_stream(self, history, prompt, memory):
        pass

    @staticmethod
    def get_completion_service(model_service_provider, model_name, base_url, api_key, **kwargs):
        kwargs["model"] = model_name
        kwargs["api_key"] = api_key
        kwargs["base_url"] = base_url
        predictor = CompletionService(model_service_provider, model_name, base_url, api_key, kwargs)
        return predictor(**kwargs)
