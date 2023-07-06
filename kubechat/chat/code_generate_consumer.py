import inspect
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from kubechat.auth.validator import DEFAULT_USER
import requests
import config.settings as settings
from channels.generic.websocket import WebsocketConsumer
from kubechat.utils.db import  query_collection, query_chat
from kubechat.utils.utils import extract_code_chat, now_unix_milliseconds, extract_collection_and_chat_id
from services.code.code_gerenate.chat_to_files import to_files
from services.code.code_gerenate.storage import DBs, DB, archive

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


first_status = {
    "DEFAULT": "clarify",
    "BENCHMARK": "simple_gen",
    "SIMPLE": "simple_gen",
    "TDD": "gen_spec",
    "TDD+": "gen_spec",
    "CLARIFY": "clarify",
    "RESPEC": "gen_spec",
    "USE_FEEDBACK": "use_feedback"
}


def fsystem(msg):
    return {"role": "system", "content": msg}


def fuser(msg):
    return {"role": "user", "content": msg}


def fassistant(msg):
    return {"role": "assistant", "content": msg}


def get_prompt(dbs: DBs) -> str:
    """While we migrate we have this fallback getter"""
    assert (
            "prompt" in dbs.input or "main_prompt" in dbs.input
    ), "Please put your prompt in the file `prompt` in the project directory"

    if "prompt" not in dbs.input:
        print(
            "Please put the prompt in the file `prompt`, not `main_prompt"
        )
        print()
        return dbs.input["main_prompt"]

    return dbs.input["prompt"]


def setup_sys_prompt(dbs: DBs) -> str:
    return (
            dbs.preprompts["generate"] + "\nUseful to know:\n" + dbs.preprompts["philosophy"]
    )


def curr_fn() -> str:
    """Get the name of the current function"""
    return inspect.stack()[1].function


class CodeGenerateConsumer(WebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.user = DEFAULT_USER
        self.status = {}
        self.current_status = "init"
        self.dbs = None
        self.type = ""
        self.response_type = "code_generate"
        self.message = None

    def connect(self):
        # 在连接建立时执行的代码
        self.user = self.scope["X-USER-ID"]
        # todo: reuse collection and chat
        collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        collection = query_collection(self.user, collection_id)
        if collection is None:
            raise Exception("Collection not found")
        chat = query_chat(self.user, collection_id, chat_id)
        # chat_id = extract_code_chat(self.scope["path"])
        # collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        # chat = query_code_chat(self.user, chat_id=chat_id)
        self.type = chat.codetype
        project_path = Path.cwd() / self.user / (chat.title + str(chat_id))
        memory_path = project_path / "memory"
        workspace_path = project_path / "workspace"
        archive_path = project_path / "archive"

        self.dbs = DBs(
            memory=DB(memory_path),  # 对话记录
            logs=DB(memory_path / "logs"),  # 日志
            input=DB(project_path),
            workspace=DB(workspace_path),  # code项目存放路径
            preprompts=DB(code_default_path),  # 默认preprompts的路径
            archive=DB(archive_path),
        )
        self.dbs.input["prompt"] = chat.summary  # write the core prompt for code-generate
        archive(self.dbs)
        self.current_status = first_status.get(self.type)
        # maybe more interact
        self.message, self.current_status = self.clarify_start()
        if self.current_status == "clarified":
            self.dbs.logs["clarify"] = json.dumps(self.message)
            self.clarified()

    def disconnect(self, close_code):
        # 在连接关闭时执行的代码
        pass

    def receive(self, text_data):
        # 在接收到消息时执行的代码
        data = json.loads(text_data)
        self.message, self.current_status = self.clarifying(data["data"], self.message)
        if self.current_status == "clarified":
            self.dbs.logs["clarify"] = json.dumps(self.message)
            self.clarified()

    def clarify_start(self) -> (List[dict], str):
        messages = [fsystem(msg=self.dbs.preprompts["qa"])]
        user_input = get_prompt(self.dbs)
        messages = self.interact_with_LLM(messages=messages, prompt=user_input, step_name=curr_fn())
        if messages[-1]["content"].strip() == "Nothing more to clarify." or messages[-1][
            "content"].strip().lower().startswith("no"):
            return messages, "clarified"
        message_id = f"{now_unix_milliseconds()}"
        response = self.success_response(
            message_id, '(answer in text, or "c" to move on)\n', issql=self.response_type == "sql"
        )
        self.send(text_data=response)
        return messages, "clarifying"

    def clarifying(self, user_input, massage: List[dict]):
        if not user_input or user_input == "c":
            message_id = f"{now_unix_milliseconds()}"
            response = self.success_response(
                message_id, '(letting gpt-engineer make its own assumptions)\n', issql=self.response_type == "sql"
            )
            self.send(text_data=response)
            return massage, "clarified"

        user_input += (
            "\n\n"
            "Is anything else unclear? If yes, only answer in the form:\n"
            "{remaining unclear areas} remaining questions.\n"
            "{Next question}\n"
            'If everything is sufficiently clear, only answer "Nothing more to clarify.".'
        )
        massage = self.interact_with_LLM(massage, user_input, step_name=curr_fn())
        if massage[-1]["content"].strip() == "Nothing more to clarify." or massage[-1][
            "content"].strip().lower().startswith("no"):
            return massage, "clarified"

        message_id = f"{now_unix_milliseconds()}"
        response = self.success_response(
            message_id, '(answer in text, or "c" to move on)\n', issql=self.response_type == "sql"
        )
        self.send(text_data=response)
        return massage, "clarifying"

    def clarified(self):
        for step in [self.gen_clarified_code, self.gen_entrypoint]:
            messages = step()
            self.dbs.logs[step.__name__] = json.dumps(messages)

    def interact_with_LLM(self, messages: List[Dict[str, str]], prompt=None, *, step_name=None):
        if prompt:
            messages += [{"role": "user", "content": prompt}]
        input = {
            "prompt": json.dumps(messages),
            "temperature": 0,
            "max_new_tokens": 2048,
            "model": "vicuna-13b",
            "stop": "\nSQLResult:",
        }

        response = requests.post(
            "%s/generate_stream" % settings.MODEL_SERVER, json=input, stream=True
        )
        message_id = f"{now_unix_milliseconds()}"
        self.send(text_data=self.start_response(message_id))
        chat = []
        for chunk in response:
            delta = chunk["choices"][0]["delta"]  # type: ignore
            msg = delta.get("content", "")
            response = self.success_response(
                message_id, msg, issql=self.response_type == "sql"
            )
            self.send(text_data=response)
            chat.append(msg)
        messages += [{"role": "assistant", "content": "".join(chat)}]
        logger.debug(f"Chat completion finished: {messages}")
        return messages

    def gen_clarified_code(self) -> List[dict]:
        messages = json.loads(self.dbs.logs["clarify"])
        messages = [
                       fsystem(setup_sys_prompt(self.dbs)),
                   ] + messages[1:]
        messages = self.interact_with_LLM(messages, self.dbs.preprompts["use_qa"], step_name=curr_fn())
        to_files(messages[-1]["content"], self.dbs.workspace)
        return messages

    def gen_entrypoint(self) -> List[dict]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You will get information about a codebase that is currently on disk in "
                    "the current folder.\n"
                    "From this you will answer with code blocks that includes all the necessary "
                    "unix terminal commands to "
                    "a) install dependencies "
                    "b) run all necessary parts of the codebase (in parallel if necessary).\n"
                    "Do not install globally. Do not use sudo.\n"
                    "Do not explain the code, just give the commands.\n"
                    "Do not use placeholders, use example values (like . for a folder argument) "
                    "if necessary.\n")
            },
            {
                "role": "user",
                "content": "Information about the codebase:\n\n" + self.dbs.workspace["all_output.txt"]
            },
        ]
        return self.interact_with_LLM(messages, step_name=curr_fn())

    @staticmethod
    def success_response(message_id, data, issql=False):
        return json.dumps(
            {
                "type": "message" if not issql else "sql",
                "id": message_id,
                "data": data,
                "timestamp": now_unix_milliseconds(),
            }
        )

    @staticmethod
    def fail_response(message_id, error):
        return json.dumps(
            {
                "type": "error",
                "id": message_id,
                "data": error,
                "timestamp": now_unix_milliseconds(),
            }
        )

    @staticmethod
    def start_response(message_id):
        return json.dumps(
            {
                "type": "start",
                "id": message_id,
                "timestamp": now_unix_milliseconds(),
            }
        )

    @staticmethod
    def stop_response(message_id, references):
        if references is None:
            references = []
        return json.dumps(
            {
                "type": "stop",
                "id": message_id,
                "data": references,
                "timestamp": now_unix_milliseconds(),
            }
        )
