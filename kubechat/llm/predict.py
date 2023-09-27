import asyncio
import json
import os
from abc import ABC, abstractmethod
from enum import Enum

import openai
import requests


class PredictorType(Enum):
    KB_VLLM = "kb-vllm"
    CUSTOM_LLM = "custom-llm"
    OPENAI_GPT_3_5 = "chatgpt-3.5"
    OPENAI_GPT_4 = "chatgpt-4"


class Predictor(ABC):

    def __init__(self, **kwargs):
        self.max_tokens = kwargs.get("max_tokens", 4096)
        self.temperature = kwargs.get("temperature", 0.1)

    @abstractmethod
    async def agenerate_stream(self, prompt):
        pass

    @abstractmethod
    def generate_stream(self, prompt):
        pass

    @staticmethod
    def get_model_context(model_name):
        model_servers = json.loads(os.environ.get("MODEL_SERVERS", "{}"))
        if len(model_servers) == 0:
            raise Exception("No model server available")
        for model_server in model_servers:
            if model_name == model_server["name"]:
                return model_server
        return None

    @staticmethod
    def from_model(model_name="", predictor_type="", endpoint="", **kwargs):
        if model_name == "chatgpt-3.5":
            return OpenAIPredictor(model="gpt-3.5-turbo", endpoint=endpoint, **kwargs)
        elif model_name == "chatgpt-4":
            return OpenAIPredictor(model="gpt-4", endpoint=endpoint, **kwargs)

        if not endpoint:
            ctx = Predictor.get_model_context(model_name)
            if not ctx:
                raise Exception("No model server available for model: %s" % model_name)
            endpoint = ctx.get("endpoint", "")
            predictor_type = ctx.get("type", PredictorType.CUSTOM_LLM)

        match predictor_type:
            case PredictorType.KB_VLLM:
                return KubeBlocksLLMPredictor(endpoint=endpoint, **kwargs)
            case PredictorType.CUSTOM_LLM:
                return CustomLLMPredictor(endpoint=endpoint, **kwargs)
            case _:
                raise Exception("Unsupported predictor type: %s" % predictor_type)


class KubeBlocksLLMPredictor(Predictor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = kwargs.get("endpoint", "http://localhost:18000")

    def _generate_stream(self, prompt):
        input = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        response = requests.post("%s/generate" % self.endpoint, json=input, stream=True)
        output = prompt
        for chunk in response.iter_lines(chunk_size=2048, decode_unicode=False, delimiter=b"\0"):
            if chunk:
                data = json.loads(chunk.decode("utf-8"))
                tokens = data["text"][0][len(output):]
                yield tokens
                output = data["text"][0]

    async def agenerate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens
            await asyncio.sleep(0.1)

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens


class CustomLLMPredictor(Predictor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", "baichuan-13b")
        self.endpoint = kwargs.get("endpoint", "http://localhost:18001")

    def _generate_stream(self, prompt):
        data = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_new_tokens": self.max_tokens,
            "model": self.model,
            "stop": "\nSQLResult:",
        }

        response = requests.post("%s/generate_stream" % self.endpoint, json=data, stream=True)
        for chunk in response.iter_lines(chunk_size=2048, decode_unicode=False, delimiter=b"\0"):
            if chunk:
                data = json.loads(chunk.decode("utf-8"))
                yield data["text"]

    async def agenerate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens
            await asyncio.sleep(0.1)

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens


class OpenAIPredictor(Predictor):
    def __init__(self, model="gpt-3.5-turbo", **kwargs):
        super().__init__(**kwargs)
        self.endpoint = kwargs.get("endpoint", "https://api.openai.com/v1")
        self.token = kwargs.get("token", "nan")
        self.model = model

    def _generate_stream(self, prompt):
        response = openai.ChatCompletion.create(
            api_key=self.token,
            api_base=self.endpoint,
            stream=True,
            model=self.model,
            messages=[{"role": "user", "content": prompt}])
        for chunk in response:
            choices = chunk["choices"]
            if len(choices) > 0:
                choice = choices[0]
                if choice["finish_reason"] == "stop":
                    return
                content = choice["delta"]["content"]
                yield content

    async def agenerate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens
            await asyncio.sleep(0.1)

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens
