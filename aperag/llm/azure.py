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
import os

import httpx
import litellm
import openai

from aperag.llm.base import LLMConfigError, Predictor


class AzureOpenAIPredictor(Predictor):
    """
    https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/switching-endpoints#keyword-argument-for-model
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.trial:
            self.deployment_id = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "")
            self.endpoint = os.environ.get("AZURE_OPENAI_API_BASE", "")
            self.api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "")
            self.token = os.environ.get("AZURE_OPENAI_API_KEY", "")
        else:
            self.deployment_id = kwargs.get("deployment_id", "")
            self.endpoint = kwargs.get("endpoint", "")
            self.api_version = kwargs.get("api_version", "")
            self.token = kwargs.get("token", "")

        self.endpoint = self.endpoint.strip()
        self.token = self.token.strip()

        if not self.deployment_id:
            raise LLMConfigError("Please specify the deployment ID")

        if not self.endpoint:
            raise LLMConfigError("Please specify the API endpoint")

        if not self.api_version:
            raise LLMConfigError("Please specify the API version")

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

    @staticmethod
    def provide_default_token():
        return bool(os.environ.get("OPENAI_API_KEY", ""))

    async def _agenerate_stream(self, history, prompt, memory=False):
        response = litellm.completion(
            model=self.deployment_id,
            stream=True,
            temperature=self.temperature,
            messages=history + [{"role": "user", "content": prompt}] if memory else [{"role": "user", "content": prompt}],
            timeout=httpx.Timeout(None, connect=3),
            api_key=self.token,
            api_version=self.api_version,
            max_retries=0,
            base_url=self.endpoint,
        )
        async for chunk in response:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if choice.finish_reason == "stop":
                return
            content = choice.delta.content
            if not content:
                continue
            yield choice.delta.content

    def _generate_stream(self, history, prompt, memory=False):
        response = litellm.completion(
            model=self.deployment_id,
            stream=True,
            temperature=self.temperature,
            messages=history + [{"role": "user", "content": prompt}] if memory else [
                {"role": "user", "content": prompt}],
            timeout=httpx.Timeout(None, connect=3),
            api_key=self.token,
            api_version=self.api_version,
            max_retries=0,
            base_url=self.endpoint,
        )
        for chunk in response:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if choice.finish_reason == "stop":
                return
            content = choice.delta.content
            if not content:
                continue
            yield choice.delta.content

    async def agenerate_stream(self, history, prompt, memory=False):
        async for tokens in self._agenerate_stream(history, prompt, memory):
            yield tokens

    def generate_stream(self, history, prompt, memory=False):
        for tokens in self._generate_stream(history, prompt, memory):
            yield tokens
