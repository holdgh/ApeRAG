import json
import logging
from config import settings

from langchain import PromptTemplate
from .base_consumer import BaseConsumer
from .prompts import DEFAULT_MODEL_PROMPT_TEMPLATES, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2
from kubechat.chat.websocket.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


def get_endpoint(model):
    model_servers = json.loads(settings.MODEL_SERVERS)
    if len(model_servers) == 0:
        raise Exception("No model server available")
    endpoint = model_servers[0]["endpoint"]
    for model_server in model_servers:
        model_name = model_server["name"]
        model_endpoint = model_server["endpoint"]
        if model == model_name:
            endpoint = model_endpoint
            break
    return endpoint


class ChatBotConsumer(BaseConsumer):
    def __init__(self):
        super().__init__()
        self.chat_limit = 2

    async def predict(self, query):
        history_context = ""
        count = 0
        for message in self.history.messages:
            content = json.loads(message.content)
            if count % 2 == 0:
                history_context += "human: " + content.get("data", " ") + "\n"
                count += 1
            else:
                history_context += "ai: " + content.get("data", " ") + "\n"
                count += 1
        history_context = history_context.strip()

        bot_config = json.loads(self.bot.config)
        llm_config = bot_config.get("llm", {})
        model = bot_config.get("model", "")
        prompt_template = llm_config.get("prompt_template", None)
        if not prompt_template:
            prompt_template = DEFAULT_MODEL_PROMPT_TEMPLATES.get(model, DEFAULT_CHINESE_PROMPT_TEMPLATE_V2)
        prompt = PromptTemplate.from_template(prompt_template)
        prompt_str = prompt.format(query=query, context=history_context[-2000:])

        # choose llm model
        endpoint = get_endpoint(model)
        factory = LLMFactory()
        llm = factory.create_llm(model)
        for text in llm.generate_stream(prompt=prompt_str, model=model, llm_config=llm_config, endpoint=endpoint):
            yield text
