import json
import os

import openai

from kubechat.llm.base import Predictor, LLMConfigError


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

    async def _agenerate_stream(self, history, prompt, memory=False):
        response = await openai.ChatCompletion.acreate(
            api_key=self.token,
            api_base=self.endpoint,
            api_type=self.api_type,
            api_version=self.api_version,
            temperature=self.temperature,
            stream=True,
            deployment_id=self.deployment_id,
            messages=history + [{"role": "user", "content": prompt}] if memory else [{"role": "user", "content": prompt}]
        )
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

    def _generate_stream(self, history, prompt, memory=False):
        response = openai.ChatCompletion.create(
            api_key=self.token,
            api_base=self.endpoint,
            api_type=self.api_type,
            api_version=self.api_version,
            temperature=self.temperature,
            stream=True,
            deployment_id=self.deployment_id,
            messages=history + [{"role": "user", "content": prompt}] if memory else [{"role": "user", "content": prompt}]
        )
        for chunk in response:
            choices = chunk["choices"]
            if len(choices) > 0:
                choice = choices[0]
                if choice["finish_reason"] == "stop":
                    return
                content = choice["delta"]["content"]
                yield content

    async def agenerate_stream(self, history, prompt, memory=False):
        async for tokens in self._agenerate_stream(history, prompt, memory):
            yield tokens

    def generate_stream(self, history, prompt, memory=False):
        for tokens in self._generate_stream(history, prompt, memory):
            yield tokens
