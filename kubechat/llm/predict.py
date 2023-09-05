import asyncio
import json
from abc import ABC, abstractmethod

import requests


class Predictor(ABC):

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    async def agenerate_stream(self, prompt):
        pass

    @abstractmethod
    def generate_stream(self, prompt):
        pass


def get_predictor(model, model_servers):
    if len(model_servers) == 0:
        raise Exception("No model server available")
    endpoint = model_servers[0]["endpoint"]
    for model_server in model_servers:
        model_name = model_server["name"]
        model_endpoint = model_server["endpoint"]
        if model == model_name:
            endpoint = model_endpoint
            break

    match model:
        case "baichuan-13b" | "vicuna-13b" | "internlm-chat-7b":
            return CustomLLMPredictor(endpoint=endpoint)
        case "openai":
            raise Exception("Unsupported model: %s" % model)
        case _:
            raise Exception("Unsupported model: %s" % model)


class CustomLLMPredictor(Predictor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", "baichuan-13b")
        self.endpoint = kwargs.get("endpoint", "http://localhost:18000")

    async def agenerate_stream(self, prompt):
        data = {
            "prompt": prompt,
            "temperature": 0,
            "max_new_tokens": 2048,
            "model": self.model,
            "stop": "\nSQLResult:",
        }

        response = requests.post("%s/generate_stream" % self.endpoint, json=data, stream=True)
        buffer = ""
        for c in response.iter_content():
            if c == b"\x00":
                continue

            c = c.decode("utf-8")
            buffer += c

            if "}" in c:
                idx = buffer.rfind("}")
                data = buffer[: idx + 1]
                try:
                    msg = json.loads(data)
                except Exception as e:
                    continue
                yield msg["text"]
                await asyncio.sleep(0.1)
                buffer = buffer[idx + 1:]

    def generate_stream(self, prompt):
        data = {
            "prompt": prompt,
            "temperature": 0,
            "max_new_tokens": 2048,
            "model": "baichuan-13b",
            "stop": "\nSQLResult:",
        }

        response = requests.post("%s/generate_stream" % self.endpoint, json=data, stream=True)
        buffer = ""
        result = ""
        for c in response.iter_content():
            if c == b"\x00":
                continue

            c = c.decode("utf-8")
            buffer += c

            if "}" in c:
                idx = buffer.rfind("}")
                data = buffer[: idx + 1]
                try:
                    msg = json.loads(data)
                except Exception as e:
                    continue
                result += msg["text"]
                buffer = buffer[idx + 1:]
        return result
