import hashlib
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum

import aiohttp
import jwt
import openai
import qianfan
import zhipuai
import requests

logger = logging.getLogger(__name__)


class PredictorType(Enum):
    KB_VLLM = "kb-vllm"
    CUSTOM_LLM = "custom-llm"


class LLMConfigError(Exception):
    """
    LLMConfigError is raised when the LLM config is invalid.
    """


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
    def from_model(model_name, predictor_type="", **kwargs):
        match model_name:
            case "chatgpt-3.5":
                kwargs["model"] = "gpt-3.5-turbo"
                return OpenAIPredictor(**kwargs)
            case "gpt-3.5-turbo-1106" | "gpt-3.5-turbo" | "gpt-3.5-turbo-16k" | "gpt-3.5-turbo-instruct":
                return OpenAIPredictor(**kwargs)
            case "chatgpt-4":
                kwargs["model"] = "gpt-4"
                return OpenAIPredictor(**kwargs)
            case "gpt-4-1106-preview" | "gpt-4-vision-preview" | "gpt-4" | "gpt-4-32k" | "gpt-4-0613" | "gpt-4-32k-0613":
                return OpenAIPredictor(**kwargs)
            case "azure-openai":
                return AzureOpenAIPredictor(**kwargs)
            case "baichuan-53b":
                return BaiChuanPredictor(**kwargs)
            case "ernie-bot-turbo":
                return BaiduQianFan(**kwargs)
            case "chatglm-pro" | "chatglm-std" | "chatglm-lite":
                kwargs["model"] = model_name.replace("-", "_")
                return ChatGLMPredictor(**kwargs)

        endpoint = kwargs.get("endpoint", "")
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

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens


class CustomLLMPredictor(Predictor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", "baichuan-13b")
        endpoint = kwargs.get("endpoint", "http://localhost:18000")
        self.url = "%s/generate_stream" % endpoint

    async def _agenerate_stream(self, prompt):
        data = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_new_tokens": self.max_tokens,
            "model": self.model,
            "stop": "\nSQLResult:",
        }

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(self.url, json=data) as r:
                while True:
                    line = await r.content.readuntil(b"\0")
                    if not line:
                        break
                    line = line.strip(b"\0")
                    yield json.loads(line.decode("utf-8"))["text"]

    def _generate_stream(self, prompt):
        data = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_new_tokens": self.max_tokens,
            "model": self.model,
            "stop": "\nSQLResult:",
        }

        response = requests.post(self.url, json=data, stream=True)
        for chunk in response.iter_lines(chunk_size=2048, decode_unicode=False, delimiter=b"\0"):
            if chunk:
                data = json.loads(chunk.decode("utf-8"))
                yield data["text"]

    async def agenerate_stream(self, prompt):
        async for tokens in self._agenerate_stream(prompt):
            yield tokens

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens


class OpenAIPredictor(Predictor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", "gpt-3.5-turbo")
        self.endpoint = kwargs.get("endpoint", "https://api.openai.com/v1")

        self.token = kwargs.get("token", os.environ.get("OPENAI_API_KEY", ""))
        if not self.token:
            raise LLMConfigError("Please specify the API token")
        """
        # https://github.com/openai/openai-python/issues/279
        Example:
        openai.proxy = {
            "http":"http://127.0.0.1:7890",
            "https":"http://127.0.0.1:7890"
        }
        """
        proxy = json.loads(os.environ.get("OPENAI_API_PROXY", "{}"))
        if proxy:
            openai.proxy = proxy

        self.api_type = ""

    async def _agenerate_stream(self, prompt):
        response = await openai.ChatCompletion.acreate(
            api_key=self.token,
            api_base=self.endpoint,
            stream=True,
            model=self.model,
            messages=[{"role": "user", "content": prompt}])
        async for chunk in response:
            choices = chunk["choices"]
            if len(choices) > 0:
                choice = choices[0]
                if choice["finish_reason"] == "stop":
                    return
                content = choice["delta"]["content"]
                yield content

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
        async for tokens in self._agenerate_stream(prompt):
            yield tokens

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens


class AzureOpenAIPredictor(Predictor):
    """
    https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/switching-endpoints#keyword-argument-for-model
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deployment_id = kwargs.get("deployment_id", "gpt-4")
        self.endpoint = kwargs.get("endpoint", "https://api.openai.com/v1")
        self.api_version = kwargs.get("api_version", "2023-05-15")

        self.token = kwargs.get("token", os.environ.get("OPENAI_API_KEY", ""))
        if not self.token:
            raise LLMConfigError("Please specify the API token")
        """
        # https://github.com/openai/openai-python/issues/279
        Example:
        openai.proxy = {
            "http":"http://127.0.0.1:7890",
            "https":"http://127.0.0.1:7890"
        }
        """
        proxy = json.loads(os.environ.get("OPENAI_API_PROXY", "{}"))
        if proxy:
            openai.proxy = proxy
        self.api_type = "azure"

    async def _agenerate_stream(self, prompt):
        response = await openai.ChatCompletion.acreate(
            api_key=self.token,
            api_base=self.endpoint,
            api_type=self.api_type,
            api_version=self.api_version,
            stream=True,
            deployment_id=self.deployment_id,
            messages=[{"role": "user", "content": prompt}])
        async for chunk in response:
            choices = chunk["choices"]
            if len(choices) > 0:
                choice = choices[0]
                if choice["finish_reason"] == "stop":
                    return
                content = choice["delta"].get("content", None)
                if not content:
                    continue
                yield content

    def _generate_stream(self, prompt):
        response = openai.ChatCompletion.create(
            api_key=self.token,
            api_base=self.endpoint,
            api_type=self.api_type,
            api_version=self.api_version,
            stream=True,
            deployment_id=self.deployment_id,
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
        async for tokens in self._agenerate_stream(prompt):
            yield tokens

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens


class BaiChuanPredictor(Predictor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url = kwargs.get("url", "https://api.baichuan-ai.com/v1/stream/chat")

        self.api_key = kwargs.get("api_key", os.environ.get("BAICHUAN_API_KEY", ""))
        if not self.api_key:
            raise LLMConfigError("Please specify the API Key")

        self.secret_key = kwargs.get("secret_key", os.environ.get("BAICHUAN_SECRET_KEY", ""))
        if not self.secret_key:
            raise LLMConfigError("Please specify the Secret Key")

    @staticmethod
    def calculate_md5(input_string):
        md5 = hashlib.md5()
        md5.update(input_string.encode('utf-8'))
        encrypted = md5.hexdigest()
        return encrypted

    @staticmethod
    def build_request_data(prompt):
        return {
            "model": "Baichuan2-53B",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        }

    def build_request_headers(self, data):
        json_data = json.dumps(data)
        time_stamp = int(time.time())
        signature = BaiChuanPredictor.calculate_md5(self.secret_key + json_data + str(time_stamp))
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
            "X-BC-Request-Id": str(uuid.uuid4()),
            "X-BC-Timestamp": str(time_stamp),
            "X-BC-Signature": signature,
            "X-BC-Sign-Algo": "MD5",
        }

    async def _agenerate_stream(self, prompt):
        data = self.build_request_data(prompt)
        headers = self.build_request_headers(data)
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(self.url, json=data, headers=headers,ssl=False) as r:
                async for line in r.content:
                    data = json.loads(line.decode("utf-8"))
                    if data["code"] != 0:
                        logger.warning("BaiChuan API error, code: %d msg: %s" % (data["code"], data["msg"]))
                        return

                    for msg in data["data"]["messages"]:
                        yield msg["content"]

    def _generate_stream(self, prompt):
        data = self.build_request_data(prompt)
        headers = self.build_request_headers(data)
        response = requests.post(self.url, data=data, headers=headers, stream=True)
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
        async for tokens in self._agenerate_stream(prompt):
            yield tokens

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
        if not self.api_key:
            raise LLMConfigError("Please specify the API Key")

        self.secret_key = kwargs.get("secret_key", os.environ.get("QIANFAN_SECRET_KEY", ""))
        if not self.secret_key:
            raise LLMConfigError("Please specify the Secret Key")

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


class ChatGLMPredictor(Predictor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = kwargs.get("endpoint", "https://open.bigmodel.cn/api/paas/v3/model-api")
        self.model = kwargs.get("model", "chatglm_lite")

        self.temperature = kwargs.get("temperature", 0.95)
        self.top_p = kwargs.get("top_p", 0.7)

        if self.model not in ["chatglm_pro", "chatglm_std", "chatglm_lite"]:
            raise LLMConfigError("Please specify the correct model")

        zhipuai.api_key = kwargs.get("api_key", os.environ.get("GLM_API_KEY", ""))
        if not zhipuai.api_key:
            raise LLMConfigError("Please specify the API KEY")

    @staticmethod
    def build_request_data(prompt):
        return {
            "prompt": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        }

    def generate_token(self, apikey: str, exp_seconds: int):
        try:
            id, secret = apikey.split(".")
        except Exception as e:
            raise Exception("invalid apikey", e)

        payload = {
            "api_key": id,
            "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
            "timestamp": int(round(time.time() * 1000)),
        }

        return jwt.encode(
            payload,
            secret,
            algorithm="HS256",
            headers={"alg": "HS256", "sign_type": "SIGN"},
        )

    def build_request_headers(self, api_key):
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.generate_token(api_key, 60),
            "accept": "text/event-stream",
        }

    async def _agenerate_stream(self, prompt):

        data = self.build_request_data(prompt)
        headers = self.build_request_headers(zhipuai.api_key)
        url = "%s/%s/sse-invoke" % (self.endpoint, self.model)
        params = {
            "temperature": self.temperature,
            "top_p": self.top_p
        }

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(url, params=params, json=data, headers=headers) as r:
                async for line in r.content:
                    if line == b'\n':
                        continue

                    key, value = line.decode("utf-8").split(":", 1)
                    if value[:-1] != "":     # 跳过回答中不该删的换行符
                        value = value[:-1]   # 删除格式里自带的换行符

                    if key == "event":
                        if value == "add":
                            continue
                        elif value == "finish":
                            return
                        else:
                            logger.warning("ChatGLM API error")
                    elif key == "data":
                        yield value

    def _generate_stream(self, prompt):
        response = zhipuai.model_api.sse_invoke(
            model=self.model,
            prompt=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            top_p=self.top_p,
        )

        for event in response.events():
            if event.event == "add":
                yield event.data
            elif event.event == "finish":
                return
            elif event.event == "error" or event.event == "interrupted":
                logger.warning("ChatGLM API error:%s" % event.data)
                return

    async def agenerate_stream(self, prompt):
        async for tokens in self._agenerate_stream(prompt):
            yield tokens

    def generate_stream(self, prompt):
        for tokens in self._generate_stream(prompt):
            yield tokens

