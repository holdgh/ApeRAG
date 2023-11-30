import asyncio
import json
from dataclasses import dataclass
from langchain.memory import RedisChatMessageHistory
from langchain.schema import AIMessage, HumanMessage
from kubechat.auth.validator import DEFAULT_USER
import config.settings as settings
from channels.generic.websocket import AsyncWebsocketConsumer

from kubechat.chat.utils import stop_response, success_response, start_response
from kubechat.tasks.code_generate import *
from kubechat.db.ops import query_collection, query_chat
from kubechat.utils.utils import now_unix_milliseconds, extract_collection_and_chat_id
from kubechat.utils.constant import KEY_USER_ID, KEY_WEBSOCKET_PROTOCOL
from services.code.code_gerenate.chat_to_files import to_files

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


class CodeGenerateConsumer(AsyncWebsocketConsumer):
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

    async def connect(self):
        # accept the websocket
        headers = []
        token = self.scope.get(KEY_WEBSOCKET_PROTOCOL, None)
        if token is not None:
            headers.append((KEY_WEBSOCKET_PROTOCOL.encode("ascii"), token.encode("ascii")))
        await super(AsyncWebsocketConsumer, self).send({"type": "websocket.accept", "headers": headers})
        # build code generate task config
        self.user = self.scope[KEY_USER_ID]
        collection_id, chat_id = extract_collection_and_chat_id(self.scope["path"])
        collection = await query_collection(self.user, collection_id)
        if collection is None:
            raise Exception("Collection not found")
        chat = await query_chat(self.user, collection_id, chat_id)

        self.collection_id = collection_id
        self.chat_id = chat_id
        self.type = chat.codetype  # to enhance the way to generate code, no we don't use it
        self.title = collection.title
        self.history = RedisChatMessageHistory(
            session_id=chat_id, url=settings.MEMORY_REDIS_URL
        )
        self.current_status = chat.status
        self.dbs = DB_init(self.user, collection.title, chat_id)

        # self.load_project()  # for test

        if chat.status == ChatStatus.UPLOADED:
            # already finish the task and generate the project zip
            message_id = f"{now_unix_milliseconds()}"
            await self.send(text_data=self.upload_response(message_id))
        elif chat.status == ChatStatus.FINISHED:
            # already finish the task but not generate the project zip
            await self.load_project()
        elif chat.status == ChatStatus.CLARIFIED:
            # already finish the CLARIFYING
            await self.clarified()
        elif chat.status == ChatStatus.CLARIFYING:
            # during the CLARIFYING
            self.message = json.loads(self.dbs.logs["pre_clarify"])
        else:  # chat.status == ChatStatus.ACTIVE  pre clarify
            # 异步请求
            # pre_clarify_task_id = pre_clarify.delay(self.user, collection_id, chat_id)
            # task = AsyncResult(id=str(pre_clarify_task_id))
            # message_id = f"{now_unix_milliseconds()}"
            # self.send(start_response(message_id))
            # self.message = task.get()
            # self.send(stop_response(message_id, None))
            self.dbs.input["prompt"] = chat.summary
            self.message = [fsystem(msg=self.dbs.preprompts["qa"])]
            user_input = get_prompt(self.dbs)
            self.message = await self.interact_with_LLM(self.message, user_input)
            if self.message[-1]["content"].strip() == "Nothing more to clarify." or self.message[-1][
                "content"].strip().lower().startswith("no"):
                self.dbs.logs["clarify"] = json.dumps(self.message)
                chat.status = ChatStatus.CLARIFIED
                await chat.asave()
                await self.clarified()
            else:
                self.dbs.logs["pre_clarify"] = json.dumps(self.message)
                await self.send_clarify_tips()
                chat.status = ChatStatus.CLARIFYING
                await chat.asave()
            self.remember_openAI_message(self.message)
            self.current_status = chat.status

    async def disconnect(self, close_code):
        # 在连接关闭时执行的代码
        pass

    async def receive(self, text_data=None, bytes_data=None):
        # only in clarifying status could step in this func
        self.history.add_message(
            HumanMessage(content=text_data, additional_kwargs={"role": "human"})
        )
        chat = await query_chat(self.user, self.collection_id, self.chat_id)
        if chat.status == ChatStatus.CLARIFYING:
            data = json.loads(text_data)
            self.message, chat.status = await self.clarifying(data["data"], self.message)
            await chat.asave()
            if chat.status == ChatStatus.CLARIFIED:
                # todo add history
                self.dbs.logs["clarify"] = json.dumps(self.message)
                # chat.task
                await self.clarified()

    async def clarifying(self, user_input, massage: List[dict]):
        if not user_input or user_input == "c":
            message_id = f"{now_unix_milliseconds()}"
            await self.send(text_data=start_response(message_id))
            response = success_response(
                message_id, '(letting gpt-engineer make its own assumptions)\n', issql=self.response_type == "sql"
            )
            await self.send(text_data=response)
            await self.send(text_data=stop_response(message_id, None))
            return massage, ChatStatus.CLARIFIED

        user_input += (
            "\n\n"
            "Is anything else unclear? If yes, only answer in the form:\n"
            "{remaining unclear areas} remaining questions.\n"
            "{Next question}\n"
            'If everything is sufficiently clear, only answer "Nothing more to clarify.".'
        )
        massage = await self.interact_with_LLM(massage, user_input, step_name=curr_fn())
        if massage[-1]["content"].strip() == "Nothing more to clarify." or massage[-1][
            "content"].strip().lower().startswith("no"):
            return massage, ChatStatus.CLARIFIED

        await self.send_clarify_tips()
        return massage, ChatStatus.CLARIFYING

    async def clarified(self):
        for step in [self.gen_clarified_code, self.gen_entrypoint]:
            messages = await step()
            self.dbs.logs[step.__name__] = json.dumps(messages)
        chat = await query_chat(self.user, self.collection_id, self.chat_id)
        chat.status = ChatStatus.FINISHED
        await chat.asave()
        await self.load_project()

    async def interact_with_LLM(self, messages: List[Dict[str, str]], prompt=None, *, step_name=None):
        '''
        interact_with_LLM is the hub between the front and LLM.
        :param messages:
        :param prompt:
        :param step_name:
        :return:
        '''
        if prompt:
            messages += [{"role": "user", "content": prompt}]
        # todo: support chose different model here
        response = openai.ChatCompletion.create(
            messages=messages,
            stream=True,
            model="gpt-3.5-turbo",
            temperature=0.1,
        )
        message_id = f"{now_unix_milliseconds()}"
        await self.send(text_data=start_response(message_id))
        chat = []
        for chunk in response:
            delta = chunk["choices"][0]["delta"]  # type: ignore
            msg = delta.get("content", "")
            response = success_response(
                message_id, msg, issql=self.response_type == "sql"
            )
            await asyncio.sleep(0.1)
            await self.send(text_data=response)
            chat.append(msg)
        await self.send(text_data=stop_response(message_id, None))
        messages += [{"role": "assistant", "content": "".join(chat)}]
        logger.debug(f"Chat completion finished: {messages}")
        return messages

    async def gen_clarified_code(self) -> List[dict]:
        messages = json.loads(self.dbs.logs["clarify"])
        messages = [
                       fsystem(setup_sys_prompt(self.dbs)),
                   ] + messages[1:]
        messages = await self.interact_with_LLM(messages, self.dbs.preprompts["use_qa"], step_name=curr_fn())
        message_id = f"{now_unix_milliseconds()}"
        self.history.add_message(
            AIMessage(
                content=success_response(
                    message_id, messages[-1]["content"], issql=self.response_type == "sql"
                ), additional_kwargs={"role": "ai"}
            ))
        to_files(messages[-1]["content"], self.dbs.workspace)
        return messages

    async def gen_entrypoint(self) -> List[dict]:
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
        messages = await self.interact_with_LLM(messages, step_name=curr_fn())
        message_id = f"{now_unix_milliseconds()}"
        self.history.add_message(
            AIMessage(
                content=success_response(
                    message_id, messages[-1]["content"], issql=self.response_type == "sql"
                ), additional_kwargs={"role": "ai"}
            ))

        return messages

    async def load_project(self):
        # project_upload = self.dbs.workspace.path / f"{self.title}.zip"
        # zip = zipfile.ZipFile(str(project_upload), 'w', zipfile.ZIP_DEFLATED)
        # for root, dirs, files in os.walk(str(self.dbs.workspace.path)):
        #     for file in files:
        #         zip.write(os.path.join(root, file), arcname=file)
        #
        # zip.close()
        message_id = f"{now_unix_milliseconds()}"
        # project_upload = self.dbs.workspace.path + f"{self.title}.zip"
        await self.send(text_data=self.upload_response(message_id))
        chat = await query_chat(self.user, self.collection_id, self.chat_id)
        chat.status = ChatStatus.UPLOADED
        await chat.asave()
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
    def upload_response(message_id):
        return json.dumps(
            {
                "type": "download",
                "id": message_id,
                "data": "",
                "timestamp": now_unix_milliseconds(),
            }
        )

    async def send_clarify_tips(self):
        message_id = f"{now_unix_milliseconds()}"
        await self.send(text_data=start_response(message_id))
        response = success_response(
            message_id, '(answer in text, or "c" to move on)\n', issql=self.response_type == "sql"
        )
        await self.send(text_data=response)
        # send stop message
        await self.send(text_data=stop_response(message_id, None))

    def remember_openAI_message(self, messages):
        for elem in messages:
            if elem["role"] == "system":
                pass
            elif elem["role"] == "user":
                pass
            elif elem["role"] == "assistant":
                message_id = f"{now_unix_milliseconds()}"
                self.history.add_message(
                    AIMessage(
                        content=success_response(
                            message_id, elem["content"], issql=self.response_type == "sql"
                        ), additional_kwargs={"role": "ai"}
                    ))
