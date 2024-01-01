import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict

import requests

from .openai_chat import openai_generate_stream

logger = logging.getLogger(__name__)


def get_input(prompt, model, llm_config):
    input = {
        "prompt": prompt,
        "temperature": llm_config.get("temperature", 0),
        "max_new_tokens": llm_config.get("max_new_tokens", 2048),
        "model": model,
        "stop": llm_config.get("stop", "\nSQLResult:"),
    }
    if model == "chatgpt":
        if llm_config.get('proxy_api_key', '') == '':
            input['proxy_api_key'] = os.getenv("PROXY_API_KEY")
            input['chat_limit'] = True  # used to judge if it is needed to limit the chat
        else:
            input['proxy_api_key'] = llm_config['proxy_api_key']

        if llm_config.get('proxy_server_url', '') == '':
            input['proxy_server_url'] = os.getenv("PROXY_SERVER_URL")
        else:
            input['proxy_server_url'] = llm_config['proxy_server_url']
    return input


class LLM(ABC):
    def __init__(self):
        self.name = None
        self.chat_limit = None

    @abstractmethod
    def generate_stream(
        self,
        prompt,
        model,
        llm_config: Dict[str, Any],
        **kwargs: Any,
    ):
        pass

    @abstractmethod
    def generate(
            self,
            prompt,
            model,
            llm_config: Dict[str, Any],
            **kwargs: Any,
    ):
        pass


class CustomLLM(LLM):
    def generate_stream(
        self,
        prompt,
        model,
        llm_config: Dict[str, Any],
        **kwargs: Any,
    ):
        input = get_input(prompt, model, llm_config)
        response = requests.post("%s/generate_stream" % kwargs["endpoint"], json=input, stream=True, )
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
                except Exception:
                    continue
                yield msg["text"]
                buffer = buffer[idx + 1:]

    def generate(
            self,
            prompt,
            model,
            llm_config: Dict[str, Any],
            **kwargs: Any,
    ):
        pass


class OpenAILLM(LLM):
    def __init__(self):
        super().__init__()

    def generate_stream(
        self,
        prompt,
        model,
        llm_config: Dict[str, Any],
        **kwargs: Any,
    ):
        input = get_input(prompt, model, llm_config)
        if 'chat_limit' in input and self.chat_limit == 0:
            yield json.dumps({"ERROR": "Chat limit reached."})
        else:
            for text in openai_generate_stream(input):
                yield text

    def generate(
            self,
            prompt,
            model,
            llm_config: Dict[str, Any],
            **kwargs: Any,
    ):
        pass


class KubeBlocksLLM(LLM):
    def generate_stream(
        self,
        prompt,
        model,
        llm_config: Dict[str, Any],
        **kwargs: Any,
    ) -> str:
        input = {
            "prompt": prompt,
            "temperature": llm_config.get("temperature", 0),
            "max_tokens": llm_config.get("max_new_tokens", 64),
            "stream": True,
        }
        response = requests.post("%s/v1/completions" % kwargs["endpoint"], json=input, stream=True)
        text = ""
        for line in response.iter_lines():
            if line:
                json_data = line.split(b": ", 1)[1]
                decoded_line = json_data.decode("utf-8")
                if decoded_line.lower() != "[DONE]".lower():
                    try:
                        obj = json.loads(json_data)
                        if obj["choices"][0].get("text") is not None:
                            content = obj["choices"][0]["text"]
                            text += content
                            yield content
                    except Exception:
                        continue

    def generate(
            self,
            prompt,
            model,
            llm_config: Dict[str, Any],
            **kwargs: Any,
        ) -> str:
            input = {
                "prompt": prompt,
                "temperature": llm_config.get("temperature", 0),
                "max_tokens": llm_config.get("max_new_tokens", 10),
            }
            response = requests.post("%s/v1/completions" % kwargs["endpoint"], json=input)
            content = response.content.decode("utf-8")
            msg = json.loads(content)
            yield msg["choices"][0]["text"]


class LLMFactory:
    def create_llm(self, llm_type: str) -> LLM:
        if llm_type == "chatgpt":
            return OpenAILLM()
        elif llm_type == "KubeBlocksLLM":
            return KubeBlocksLLM()
        else:
            return CustomLLM()
