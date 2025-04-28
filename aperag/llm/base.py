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

import json
import logging
from abc import ABC, abstractmethod
from enum import Enum

import requests
import yaml

from config import settings

logger = logging.getLogger(__name__)


class PredictorType(Enum):
    CUSTOM_LLM = "custom-llm"


class LLMConfigError(Exception):
    """
    LLMConfigError is raised when the LLM config is invalid.
    """


class LLMAPIError(Exception):
    """
    LLMAPIError is raised when error occurs when calling LLM API.
    """


class Predictor(ABC):

    def __init__(self, **kwargs):
        self.max_tokens = kwargs.get("max_tokens", 4096)
        self.temperature = kwargs.get("temperature", 0.1)
        self.trial = False

    @abstractmethod
    async def agenerate_stream(self, history, prompt, memory):
        pass

    @abstractmethod
    def generate_stream(self, history, prompt, memory):
        pass

    @staticmethod
    def get_model_context(model_name):
        model_families = yaml.safe_load(settings.MODEL_FAMILIES)
        for model_family in model_families:
            for model_server in model_family.get("models", []):
                if model_name == model_server["name"]:
                    return model_server
        return None

    @staticmethod
    def match_predictor(model_name, predictor_type, kwargs):
        from aperag.llm.completion_service import CompletionService
        match model_name:
            case "chatgpt-3.5":
                kwargs["model"] = "gpt-3.5-turbo"
                return CompletionService
            case "gpt-3.5-turbo-1106" | "gpt-3.5-turbo" | "gpt-3.5-turbo-16k" | "gpt-3.5-turbo-instruct":
                return CompletionService
            case "chatgpt-4":
                kwargs["model"] = "gpt-4"
                return CompletionService
            case "deepseek-chat" | "gpt-4-1106-preview" | "gpt-4-vision-preview" | "gpt-4" | "gpt-4-32k" | "gpt-4-0613" | "gpt-4-32k-0613":
                return CompletionService
            case "glm-4-plus" | "glm-4-air" | "glm-4-long" | "glm-4-flashx" | "glm-4-flash":
                return CompletionService
            case "azure-openai":
                return CompletionService
            case "qwen-turbo" | "qwen-plus" | "qwen-max":
                from aperag.llm.qianwen import QianWenPredictor
                return QianWenPredictor

        endpoint = kwargs.get("endpoint", "")
        if not endpoint:
            ctx = Predictor.get_model_context(model_name)
            if not ctx:
                raise Exception("No model server available for model: %s" % model_name)
            endpoint = ctx.get("endpoint", "")
            kwargs["endpoint"] = endpoint
            predictor_type = ctx.get("type", PredictorType.CUSTOM_LLM)

        match predictor_type:
            case PredictorType.CUSTOM_LLM:
                from aperag.llm.custom import CustomLLMPredictor
                return CustomLLMPredictor
            case _:
                raise Exception("Unsupported predictor type: %s" % predictor_type)

    @staticmethod
    def get_completion_service(model_name, predictor_type="", **kwargs):
        predictor = Predictor.match_predictor(model_name, predictor_type, kwargs)
        return predictor(**kwargs)

    @staticmethod
    def check_default_token(model_name, predictor_type="", **kwargs):
        predictor = Predictor.match_predictor(model_name, predictor_type, kwargs)
        return predictor.provide_default_token()

    def get_latest_history(self, messages, limit_length, limit_count, use_ai_memory) -> str:
        latest_history = []
        length = 0
        count = 0

        for message in reversed(messages):
            if message.additional_kwargs["role"] == "human":
                history = {"role": "user", "content": json.loads(message.content)["query"] + "\n"}
            else:
                if not use_ai_memory:
                    continue
                history = {"role": "assistant", "content": json.loads(message.content)["response"] + "\n"}
            count += 1

            if count >= limit_count or length + len(history["content"]) > limit_length:
                break

            latest_history.append(history)
            length += len(history["content"])

        if len(latest_history) > 0 and latest_history[-1]["role"] == "assistant":
            latest_history = latest_history[:-1]

        return latest_history[::-1]

