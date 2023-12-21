import json
import logging
import traceback
import websockets

from kubechat.utils.utils import now_unix_milliseconds
from kubechat.chat.websocket.base_consumer import BaseConsumer
from kubechat.pipeline.translation_pipeline import TranslationPipeline
from kubechat.chat.utils import start_response, success_response, stop_response, fail_response, welcome_response


logger = logging.getLogger(__name__)


class TranslationConsumer(BaseConsumer):
    async def connect(self):
        await super().connect()
        self.pipeline = TranslationPipeline(bot=self.bot, collection=self.collection, history=self.history)
        self.use_default_token = self.pipeline.predictor.use_default_token

    async def predict(self, query, **kwargs):
        async for msg in self.pipeline.run(query, gen_references=True, **kwargs):
            yield msg

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        self.msg_type = data["type"]
        self.response_type = "message"
        self.file = data.get("file", None)

        message = ""
        message_id = f"{now_unix_milliseconds()}"

        try:
            # send start message
            await self.send(text_data=start_response(message_id))

            if self.use_default_token and self.conversation_limit:
                if not await self.check_quota_usage():
                    error = f"conversation rounds have reached to the limit of {self.conversation_limit}"
                    await self.send(text_data=fail_response(message_id, error=error))
                    return

            async for tokens in self.predict(data["data"], message_id=message_id, file=self.file):
                # streaming response
                response = success_response(message_id, tokens, issql=self.response_type == "sql")
                await self.send(text_data=response)

                # concat response tokens
                message += tokens

        except websockets.exceptions.ConnectionClosedError:
            logger.warning("Connection closed")
        except Exception as e:
            logger.warning("[Oops] %s: %s", str(e), traceback.format_exc())
            await self.send(text_data=fail_response(message_id, str(e)))
        finally:
            if self.use_default_token and self.conversation_limit:
                await self.manage_quota_usage()
            # send stop message
            await self.send(text_data=stop_response(message_id, [], [], self.pipeline.memory_count))
