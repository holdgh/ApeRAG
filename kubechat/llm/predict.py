import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum

import openai
import qianfan
import requests

logger = logging.getLogger(__name__)


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
        match model_name:
            case "chatgpt-3.5":
                return OpenAIPredictor(model="gpt-3.5-turbo", endpoint=endpoint, **kwargs)
            case "chatgpt-4":
                return OpenAIPredictor(model="gpt-4", endpoint=endpoint, **kwargs)
            case "baichuan-53b":
                return BaiChuanPredictor(**kwargs)
            case "ernie-bot-turbo":
                return BaiduQianFan(**kwargs)

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
        for chunk in response.iter_lines():
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
        self.token = kwargs.get("token", os.environ.get("OPENAI_API_KEY", ""))
        self.model = model

        """
        Example:
        openai.proxy = {
            "http":"http://127.0.0.1:7890",
            "https":"http://127.0.0.1:7890"
        }
        """
        proxy = json.loads(os.environ.get("OPENAI_API_PROXY", "{}"))
        if proxy:
            openai.proxy = proxy

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


class BaiChuanPredictor(Predictor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = kwargs.get("api_key", os.environ.get("BAICHUAN_API_KEY", ""))
        self.secret_key = kwargs.get("secret_key", os.environ.get("BAICHUAN_SECRET_KEY", ""))

    @staticmethod
    def calculate_md5(input_string):
        md5 = hashlib.md5()
        md5.update(input_string.encode('utf-8'))
        encrypted = md5.hexdigest()
        return encrypted

    def _generate_stream(self, prompt):
        url = "https://api.baichuan-ai.com/v1/stream/chat"

        data = {
            "model": "Baichuan2-53B",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        }

        json_data = json.dumps(data)
        time_stamp = int(time.time())
        signature = BaiChuanPredictor.calculate_md5(self.secret_key + json_data + str(time_stamp))

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
            "X-BC-Request-Id": str(uuid.uuid4()),
            "X-BC-Timestamp": str(time_stamp),
            "X-BC-Signature": signature,
            "X-BC-Sign-Algo": "MD5",
        }

        response = requests.post(url, data=json_data, headers=headers, stream=True)
        for chunk in response.iter_lines():
            if not chunk:
                continue
            data = json.loads(chunk.decode("utf-8"))
            if data["code"] != 0:
                logger.warning("BaiChuan API error, code: %d msg: %s" % (data["code"], data["msg"]))
                return

            for msg in data["data"]["messages"]:
                yield msg["content"]

    async def agenerate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens
            await asyncio.sleep(0.1)

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens


class BaiduQianFan(Predictor):
    """
    https://cloud.baidu.com/doc/WENXINWORKSHOP/s/4lilb2lpf
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = "ERNIE-Bot-turbo"
        self.api_key = kwargs.get("api_key", os.environ.get("QIANFAN_API_KEY", ""))
        self.secret_key = kwargs.get("secret_key", os.environ.get("QIANFAN_SECRET_KEY", ""))
        self.chat_comp = qianfan.ChatCompletion(ak=self.api_key, sk=self.secret_key)

    async def agenerate_stream(self, prompt):
        resp = await self.chat_comp.ado(model=self.model, stream=True,
                                        messages=[{"role": "user", "content": prompt}])
        async for chunk in resp:
            yield chunk["result"]

    def generate_stream(self, prompt):
        resp = self.chat_comp.do(model=self.model, stream=True,
                                 messages=[{"role": "user", "content": prompt}])
        yield resp['body']['result']
