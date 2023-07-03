import json
import logging
import traceback
from typing import Any, List, Mapping, Optional

import requests
from channels.generic.websocket import WebsocketConsumer
from langchain.llms.base import LLM
from langchain.memory import ConversationBufferWindowMemory

from configs.config import Config
from kubechat.utils.utils import extract_chat_id, now_unix_milliseconds

logger = logging.getLogger(__name__)

CFG = Config()


class CustomLLM(LLM):
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        input = {
            "prompt": prompt,
            "temperature": 0,
            "max_new_tokens": 2048,
            "model": "vicuna-13b",
            "stop": "\nSQLResult:",
        }
        response = requests.post("%s/generate" % CFG.MODEL_SERVER, json=input)
        return response

    def call_custom_llm(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return self._call(prompt, stop)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"name_of_model": "custom"}

    @property
    def _llm_type(self) -> str:
        return "custom"


class ChatBotConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.memory = ConversationBufferWindowMemory(k=5)  # 历史对话窗口大小
        self.llm = CustomLLM()

    def connect(self):
        from kubechat.index import init_index
        from kubechat.utils.db import query_chat

        user = self.scope["X-USER-ID"]
        chat_id = extract_chat_id(self.scope["path"])  # get the chat_id in path
        # chat = query_chat(user, chat_id) # new func, need to be verified # 这个chat好像没什么用

        # if chat is None:
        #     raise Exception("Chat not found")

        headers = {"SEC-WEBSOCKET-PROTOCOL": self.scope["Sec-Websocket-Protocol"]}
        self.accept(subprotocol=(None, headers))
        # self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data, **kwargs):
        data = json.loads(text_data)
        msg_type = data["type"]
        if msg_type == "ping":
            response = json.dumps(
                {"type": "pong", "timestamp": now_unix_milliseconds()}
            )
            self.send(text_data=response)
            return

        response_txt, references = self.predict(data["data"])  # get predict
        response = self.success_response(response_txt, references)
        # save to memory
        self.memory.save_context({"input": data["data"]}, {"output": response_txt})
        # response to user
        self.send(text_data=response)

    def predict(self, query):
        def reformat_history(buffer):
            split_history = buffer["history"].split("\n")
            formatted_history = ""
            for line in split_history:  # 从开始位置开始添加对话
                if line.startswith("Human: "):
                    formatted_history += "Human: " + line[len("Human: ") :] + "\n"
                elif line.startswith("AI: "):
                    formatted_history += "AI: " + line[len("AI: ") :] + "\n"
            return formatted_history

        buffer = self.memory.load_memory_variables({})
        history = reformat_history(buffer)
        prompt = f"""The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.
Current conversation:
{history}
human: {query}
Please complete the conversation in the role of AI, give your response, begin with "AI: " """
        stop = []

        response = self.llm.call_custom_llm(prompt, stop).text  # 约10s左右出结果
        response = response.strip("\x00")  # 去掉末尾的'\x00'
        response_dict = json.loads(response)  # 解析json字符串为字典
        text_str = response_dict["response"]  # 提取response字段的内容

        # 从字符串中获取AI的最后一句话
        start = text_str.rfind("AI: ") + 4  # 从右边找到'ai: '的位置并加4（'AI: '的长度）
        end = text_str.rfind('", "error_code":')  # 从右边找到'", "error_code":'的位置
        ai_last_sentence = text_str[start:end]  # 截取出AI的回答

        references = None
        return ai_last_sentence, references

    @staticmethod
    def success_response(message, references=None):
        if references is None:
            references = []
        return json.dumps(
            {
                "type": "message",
                "code": "200",
                "data": message,
                "timestamp": now_unix_milliseconds(),
                "references": references,
            }
        )

    @staticmethod
    def fail_response(error):
        return json.dumps(
            {
                "type": "message",
                "data": "",
                "timestamp": now_unix_milliseconds(),
                "code": "500",
                "error": error,
            }
        )
