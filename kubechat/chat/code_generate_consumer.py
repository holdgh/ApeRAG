import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from kubechat.auth.validator import DEFAULT_USER
import requests
import tiktoken
import config.settings as settings
from channels.generic.websocket import WebsocketConsumer

from kubechat.utils.db import query_code_chat
from services.code.code_gerenate.steps import STEPS, Config
from services.code.code_gerenate.storage import DBs, DB

logger = logging.getLogger(__name__)
code_default_path = Path.cwd() / "utils" / "codeprompt"


@dataclass
class TokenUsage:
    step_name: str
    in_step_prompt_tokens: int
    in_step_completion_tokens: int
    in_step_total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int


class CodeGenerateConsumer(WebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.collection_id = None
        self.embedding_model = None
        self.vector_size = 0
        self.history = None
        self.user = DEFAULT_USER

    def connect(self):
        # 在连接建立时执行的代码
        self.user = self.scope["X-USER-ID"]

    def disconnect(self, close_code):
        # 在连接关闭时执行的代码
        pass

    def receive(self, text_data):
        # 在接收到消息时执行的代码
        data = json.loads(text_data)
        chat_id = data["chat_id"]
        steps_config = data["steps"] or Config.DEFAULT
        chat = query_code_chat(self.user, chat_id=chat_id)
        steps = STEPS[steps_config]
        project_path = Path.cwd() / self.user / (chat.title + str(chat_id))
        memory_path = project_path / "memory"
        workspace_path = project_path / "workspace"
        archive_path = project_path / "archive"
        dbs = DBs(
            memory=DB(memory_path),  # 对话记录
            logs=DB(memory_path / "logs"),  # 日志
            input=DB(project_path),
            workspace=DB(workspace_path),  # code项目存放路径
            preprompts=DB(code_default_path),  # 默认preprompts的路径
            archive=DB(archive_path),
        )

    def send(self, text_data=None, bytes_data=None, close=False):
        # 发送消息到客户端的代码
        pass
