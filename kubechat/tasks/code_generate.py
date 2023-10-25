import inspect
import pathlib
from pathlib import Path
from typing import Dict, List

import openai
from config.celery import app

import logging

from config.settings import CODE_STORAGE_DIR
from kubechat.models import ChatStatus
from kubechat.tasks.index import CustomLoadDocumentTask
from kubechat.utils.db import query_collection, query_chat
from kubechat.utils.utils import fix_path_name, now_unix_milliseconds
from services.code.code_gerenate.storage import DBs, DB


logger = logging.getLogger(__name__)


@app.task(base=CustomLoadDocumentTask)
def pre_clarify(user, collection_id, chat_id):
    collection = query_collection(user, collection_id)
    chat = query_chat(user, collection_id, chat_id)
    if collection == None:
        logger.error("Collection not found")
    if chat == None:
        logger.error("Chat not found")
    dbs = DB_init(user, collection.title, chat_id)
    dbs.input["prompt"] = chat.summary  # write the core prompt for code-generate

    messages = [fsystem(msg=dbs.preprompts["qa"])]
    user_input = get_prompt(dbs)
    messages = interact_with_LLM(messages=messages, prompt=user_input, step_name=curr_fn())

    if messages[-1]["content"].strip() == "Nothing more to clarify." or messages[-1][
        "content"].strip().lower().startswith("no"):
        chat.status = ChatStatus.CLARIFIED
        chat.save()
        return messages
        # message_id = f"{now_unix_milliseconds()}"
        # self.send(text_data=stop_response(message_id, None))
    chat.status = ChatStatus.CLARIFYING
    chat.save()
    return messages


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


def DB_init(user, title, chat_id):
    base_dir = Path(CODE_STORAGE_DIR)
    project_path = base_dir / "generated-code" / fix_path_name(user) / fix_path_name(
        title + str(chat_id))
    memory_path = project_path / "memory"
    workspace_path = project_path / "workspace"
    archive_path = project_path / "archive"
    prompt_default_path = Path.cwd() / "utils" / "codeprompt"
    return DBs(
        memory=DB(memory_path),  # 对话记录
        logs=DB(memory_path / "logs"),  # 日志
        input=DB(project_path),
        workspace=DB(workspace_path),  # code项目存放路径
        preprompts=DB(prompt_default_path),  # 默认preprompts的路径
        archive=DB(archive_path),
    )


def interact_with_LLM(messages: List[Dict[str, str]], prompt=None, *, step_name=None):
    '''
    interact_with_LLM is the hub between the front and LLM. self.send(text_data=stop_response(message_id)) must
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
    # message_id = f"{now_unix_milliseconds()}"
    # self.send(text_data=start_response(message_id))
    chat = []
    for chunk in response:
        delta = chunk["choices"][0]["delta"]  # type: ignore
        msg = delta.get("content", "")
        # response = success_response(
        #     message_id, msg, issql=self.response_type == "sql"
        # )
        # self.send(text_data=response)
        chat.append(msg)
    messages += [{"role": "assistant", "content": "".join(chat)}]
    logger.debug(f"Chat completion finished: {messages}")
    return messages
