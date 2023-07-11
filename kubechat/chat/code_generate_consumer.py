import inspect
import json
import logging
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import openai
from celery.result import AsyncResult
from langchain.memory import RedisChatMessageHistory
from langchain.schema import AIMessage, HumanMessage

from kubechat.auth.validator import DEFAULT_USER
import requests
import config.settings as settings
from channels.generic.websocket import WebsocketConsumer

from kubechat.models import ChatStatus
from kubechat.tasks.code_generate import pre_clarify, fsystem, get_prompt, curr_fn, setup_sys_prompt, \
    prompt_default_path, DB_init
from kubechat.utils.db import query_collection, query_chat
from kubechat.utils.utils import extract_code_chat, now_unix_milliseconds, extract_collection_and_chat_id, fix_path_name
from services.code.code_gerenate.chat_to_files import to_files
from services.code.code_gerenate.storage import DBs, DB, archive

logger = logging.getLogger(__name__)


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


class CodeGenerateConsumer(WebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.user = DEFAULT_USER
        self.current_status = ""
        self.dbs = None
        self.type = ""
        self.response_type = "code_generate"
        self.message = None
        self.chat_id = ""
        self.collection_id = ""
        self.title = ""
        self.history = None

    def connect(self):
        headers = {}
        token = self.scope.get("Sec-Websocket-Protocol", None)
        if token is not None:
            headers = {"SEC-WEBSOCKET-PROTOCOL": token}
        self.accept(subprotocol=(None, headers))
        self.user = self.scope["X-USER-ID"]
        collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        collection = query_collection(self.user, collection_id)
        if collection is None:
            raise Exception("Collection not found")
        chat = query_chat(self.user, collection_id, chat_id)

        self.collection_id = collection_id
        self.chat_id = chat_id
        self.type = chat.codetype  # to enhance the way to generate code, no we don't use it
        self.title = collection.title
        self.history = RedisChatMessageHistory(
            session_id=chat_id, url=settings.MEMORY_REDIS_URL
        )
        self.current_status = chat.status
        # project_path = Path.cwd() / "generated-code" / fix_path_name(self.user) / fix_path_name(
        #     collection.title + str(chat_id))
        # memory_path = project_path / "memory"
        # workspace_path = project_path / "workspace"
        # archive_path = project_path / "archive"
        #
        # self.dbs = DBs(
        #     memory=DB(memory_path),  # 对话记录
        #     logs=DB(memory_path / "logs"),  # 日志
        #     input=DB(project_path),
        #     workspace=DB(workspace_path),  # code项目存放路径
        #     preprompts=DB(prompt_default_path),  # 默认preprompts的路径
        #     archive=DB(archive_path),
        # )
        self.dbs = DB_init(self.user, collection.title, chat_id)
        if chat.status == ChatStatus.FINISHED:
            self.load_project()
            chat.status = ChatStatus.UPLOADED
            chat.save()
            return
        elif chat.status == ChatStatus.CLARIFIED:
            self.clarified()
        elif chat.status == ChatStatus.CLARIFYING:
            self.message = json.loads(self.dbs.logs["pre_clarify"])
            # pass
        else:  # chat.status == ChatStatus.ACTIVE:
            pre_clarify_task_id = pre_clarify.delay(self.user, collection_id, chat_id)
            # chat.pre_clarify_task_id = pre_clarify_task_id
            # chat.save()
            task = AsyncResult(id=str(pre_clarify_task_id))
            message_id = f"{now_unix_milliseconds()}"
            self.send(self.start_response(message_id))
            self.message = task.get()
            self.dbs.logs["pre_clarify"] = json.dumps(self.message)
            self.send_openAI_message(self.message)
            chat = query_chat(self.user, collection_id, chat_id)
            self.current_status = chat.status

        # # else:
        # #     if chat.task_id == "":
        # #         chat.task_id = prompt_ask_for_clarify.delay(self.user, collection_id, chat_id)
        # #         chat.save()
        # #     task = AsyncResult(id=chat.task_id)
        # #
        # #     if task.ready():
        # #         self.message = task.result()
        # #     else:
        # #         self.message = task.get()
        # #         message_id = f"{now_unix_milliseconds()}"
        # #         self.history.add_message(
        # #             AIMessage(content=self.success_response(
        # #                 message_id, self.message, issql=self.response_type == "sql"
        # #             ), additional_kwargs={"role": "ai"})
        # #         )
        # self.current_status = chat.status
        #
        # project_path = Path.cwd() / "generated-code" / fix_path_name(self.user) / fix_path_name(
        #     collection.title + str(chat_id))
        # memory_path = project_path / "memory"
        # workspace_path = project_path / "workspace"
        # archive_path = project_path / "archive"
        #
        # self.dbs = DBs(
        #     memory=DB(memory_path),  # 对话记录
        #     logs=DB(memory_path / "logs"),  # 日志
        #     input=DB(project_path),
        #     workspace=DB(workspace_path),  # code项目存放路径
        #     preprompts=DB(prompt_default_path),  # 默认preprompts的路径
        #     archive=DB(archive_path),
        # )
        # self.dbs.input["prompt"] = chat.summary  # write the core prompt for code-generate
        # # # archive(self.dbs)
        # # self.current_status = first_status.get(self.type)
        # # # maybe more interact
        # # self.message, self.current_status = self.clarify_start()
        # # if self.current_status == "clarified":
        # #     self.dbs.logs["clarify"] = json.dumps(self.message)
        # #     self.clarified()

    def disconnect(self, close_code):
        # 在连接关闭时执行的代码
        pass

    def receive(self, text_data):
        # 在接收到消息时执行的代码
        # todo: decide whether clarified or download zip
        data = json.loads(text_data)

        self.history.add_message(
            HumanMessage(content=text_data, additional_kwargs={"role": "human"})
        )

        if self.current_status == ChatStatus.CLARIFYING:
            data = json.loads(text_data)
            self.message, self.current_status = self.clarifying(data["data"], self.message)
        if self.current_status == ChatStatus.CLARIFIED:
            # todo add history
            self.dbs.logs["clarify"] = json.dumps(self.message)
            chat = query_chat(self.user, self.collection_id, self.chat_id)
            # chat.task
            chat.status = ChatStatus.CLARIFIED
            chat.save()
            self.clarified()

    def clarifying(self, user_input, massage: List[dict]):
        if not user_input or user_input == "c":
            message_id = f"{now_unix_milliseconds()}"
            response = self.success_response(
                message_id, '(letting gpt-engineer make its own assumptions)\n', issql=self.response_type == "sql"
            )
            self.send(text_data=response)
            self.send(text_data=self.stop_response(message_id, None))
            return massage, ChatStatus.CLARIFIED

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
            message_id = f"{now_unix_milliseconds()}"
            self.send(text_data=self.stop_response(message_id, None))
            return massage, ChatStatus.CLARIFIED

        message_id = f"{now_unix_milliseconds()}"
        response = self.success_response(
            message_id, '(answer in text, or "c" to move on)\n', issql=self.response_type == "sql"
        )
        self.send(text_data=response)
        # send stop message
        self.send(text_data=self.stop_response(message_id, None))
        return massage, ChatStatus.CLARIFYING

    def clarified(self):
        for step in [self.gen_clarified_code, self.gen_entrypoint]:
            messages = step()
            self.dbs.logs[step.__name__] = json.dumps(messages)
        chat = query_chat(self.user, self.collection_id, self.chat_id)
        chat.status = ChatStatus.FINISHED
        chat.save()
        self.load_project()
        chat.status = ChatStatus.UPLOADED
        chat.save()

    def interact_with_LLM(self, messages: List[Dict[str, str]], prompt=None, *, step_name=None):
        '''
        interact_with_LLM is the hub between the front and LLM. self.send(text_data=self.stop_response(message_id)) must
         be called after interact_with_LLM.
        :param messages:
        :param prompt:
        :param step_name:
        :return:
        '''
        if prompt:
            messages += [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            messages=messages,
            stream=True,
            model="gpt-3.5-turbo",
            temperature=0.1,
        )
        # input = {
        #     "prompt": json.dumps(messages),
        #     "temperature": 0,
        #     "max_new_tokens": 2048,
        #     "model": "vicuna-13b",
        #     "stop": "\nSQLResult:",
        # }
        #
        # response = requests.post(
        #     "%s/generate_stream" % settings.MODEL_SERVER, json=input, stream=True
        # )
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
        message_id = f"{now_unix_milliseconds()}"
        self.history.add_message(
            AIMessage(
                content=self.success_response(
                    message_id, messages[-1]["content"], issql=self.response_type == "sql"
                ), additional_kwargs={"role": "ai"}
            ))
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
        messages = self.interact_with_LLM(messages, step_name=curr_fn())
        message_id = f"{now_unix_milliseconds()}"
        self.history.add_message(
            AIMessage(
                content=self.success_response(
                    message_id, messages[-1]["content"], issql=self.response_type == "sql"
                ), additional_kwargs={"role": "ai"}
            ))
        self.send(text_data=self.stop_response(message_id, None))
        return messages

    def load_project(self):
        project_upload = self.dbs.workspace.path / f"{self.title}.zip"
        zip = zipfile.ZipFile(project_upload, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(str(self.dbs.workspace.path)):
            for file in files:
                zip.write(os.path.join(root, file))
        zip.close()
        message_id = f"{now_unix_milliseconds()}"
        # project_upload = self.dbs.workspace.path + f"{self.title}.zip"
        self.send(text_data=self.upload_response(message_id, str(project_upload)))
        # change the status to
        # self.send(bytes_data=zip)

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

    @staticmethod
    def upload_response(message_id, url):
        return json.dumps(
            {
                "type": "download",
                "id": message_id,
                "data": url,
                "timestamp": now_unix_milliseconds(),
            }
        )

    def send_openAI_message(self, messages):
        for elem in messages:
            if elem["role"] == "system":
                pass
            elif elem["role"] == "user":
                pass
            elif elem["role"] == "assistant":
                message_id = f"{now_unix_milliseconds()}"
                self.send(text_data=self.start_response(message_id))
                response = self.success_response(
                    message_id, elem["content"], issql=self.response_type == "sql"
                )
                self.send(text_data=response)
                self.send(text_data=self.stop_response(message_id, None))
                self.history.add_message(
                    AIMessage(
                        content=self.success_response(
                            message_id, elem["content"], issql=self.response_type == "sql"
                        ), additional_kwargs={"role": "ai"}
                    ))
