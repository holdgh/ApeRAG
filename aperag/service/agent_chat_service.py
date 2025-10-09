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

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import WebSocket
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.agent import (
    AgentHistoryManager,
    AgentMemoryManager,
    AgentMessageQueue,
    agent_session_manager,
    extract_tool_call_references,
    format_agent_setup_error,
    format_invalid_json_error,
    format_invalid_model_spec_error,
    format_mcp_connection_error,
    format_processing_error,
    format_query_required_error,
    format_stream_content,
    format_stream_end,
    format_stream_start,
)
from aperag.agent.agent_config import AgentConfig
from aperag.agent.agent_event_listener import agent_event_listener
from aperag.agent.exceptions import (
    AgentConfigurationError,
    JSONParsingError,
    MCPAppInitializationError,
    MCPConnectionError,
    handle_agent_error,
    safe_json_parse,
)
from aperag.agent.response_types import AgentErrorResponse, AgentToolCallResultResponse
from aperag.chat.history.message import StoredChatMessage, create_assistant_message
from aperag.db.ops import AsyncDatabaseOps, async_db_ops
from aperag.schema import view_models
from aperag.service.prompt_template_service import build_agent_query_prompt, get_agent_system_prompt
from aperag.trace import trace_async_function

logger = logging.getLogger(__name__)


def format_websocket_error(error: Exception, data: str) -> AgentErrorResponse:
    try:
        parsed = safe_json_parse(data, "language_detection")
        language = parsed.get("language", "en-US")
    except Exception:
        language = "en-US"

    if isinstance(error, JSONParsingError):
        return format_invalid_json_error(str(error), language)

    if isinstance(error, AgentConfigurationError):
        error_msg = str(error).lower()
        if "query" in error_msg:
            return format_query_required_error(language)
        if "completion" in error_msg or "modelspec" in error_msg:
            return format_invalid_model_spec_error(str(error), language)

    return format_processing_error(str(error), language)


class AgentChatService:
    """
    Chat service specifically for agent-type bots that uses MCPApp for intelligent conversation.

    This service uses AgentSessionManager for efficient session lifecycle management,
    including collection selection, model choice, and web search capabilities.

    Refactored to use message queue for clean separation of concerns.
    """

    def __init__(self, session: AsyncSession = None):
        if session is None:
            self.db_ops = async_db_ops
        else:
            self.db_ops = AsyncDatabaseOps(session)

        # Initialize memory and history managers
        self.memory_manager = AgentMemoryManager()
        self.history_manager = AgentHistoryManager()

    async def _convert_db_collections_to_pydantic(self, db_collections) -> List[view_models.Collection]:  # 将机器人配置中的知识库信息列表转换为view_models.Collection实例列表
        """Convert SQLAlchemy Collection models to Pydantic Collection models"""
        from aperag.schema.utils import parseCollectionConfig

        pydantic_collections = []
        for db_collection in db_collections:
            pydantic_collection = view_models.Collection(
                id=db_collection.id,
                title=db_collection.title,
                description=db_collection.description,
                type=db_collection.type,
                status=getattr(db_collection, "status", None),
                config=parseCollectionConfig(db_collection.config),
                created=db_collection.gmt_created.isoformat(),
                updated=db_collection.gmt_updated.isoformat(),
            )
            pydantic_collections.append(pydantic_collection)
        return pydantic_collections

    def _parse_websocket_message(
        self, raw_data: str
    ) -> Tuple[Optional[view_models.AgentMessage], Optional[AgentErrorResponse]]:  # 使用go风格的错误处理解析WebSocket消息。返回view_models.AgentMessage实例
        """
        Parse WebSocket message using Go-style error handling.

        Args:
            raw_data: Raw JSON string from WebSocket

        Returns:
            Tuple of (agent_message, error_response):
            - If successful: (agent_message, None)
            - If failed: (None, error_response_dict)
        """
        try:
            # Step 1: Safe JSON parsing using agent module utilities
            message_data = safe_json_parse(raw_data, "websocket_message")  # 将前端消息解析为json数据

            # Step 2: Validate required query field early
            query = message_data.get("query", "").strip()  # 获取并校验前端消息中的query字段【必填校验】
            if not query:
                from aperag.agent.exceptions import agent_config_invalid

                error = agent_config_invalid("query", "Query is required and cannot be empty")
                error_response = format_websocket_error(error, raw_data)
                return None, error_response

            # Step 3: Parse and validate AgentMessage using Pydantic
            agent_message = view_models.AgentMessage(**message_data)  # 将前端消息封装为view_models.AgentMessage实例
            return agent_message, None

        except (JSONParsingError, AgentConfigurationError) as e:
            error_response = format_websocket_error(e, raw_data)
            return None, error_response
        except Exception as e:
            # Handle unexpected errors
            from aperag.agent.exceptions import agent_config_invalid

            config_error = agent_config_invalid("agent_message", f"Unexpected error: {str(e)}")
            error_response = format_websocket_error(config_error, raw_data)
            return None, error_response

    """
    装饰器 @handle_agent_error：
    这是一个 “异常处理装饰器”，作用是捕获函数内部抛出的异常，避免因单个错误导致 WebSocket 连接直接中断。
    参数 reraise=False 表示 “捕获异常后不向上传播”，而是由装饰器内部处理（如记录日志、返回统一格式的错误消息给前端），保证服务稳定性。
    """
    @handle_agent_error("websocket_agent_chat", reraise=False)
    async def handle_websocket_agent_chat(self, websocket: WebSocket, user: str, bot_id: str, chat_id: str):  # 基于websocket数据传输的agent对话逻辑
        """Handle WebSocket connections for agent-type bot chats with message queue architecture"""
        # -- 前置校验：获取机器人信息
        # Get bot configuration once at the beginning for performance
        bot = await self.db_ops.query_bot(user, bot_id)
        if not bot:
            error_response = format_processing_error("Bot not found", "en-US")
            await websocket.send_text(json.dumps(error_response))
            return
        # -- 解析机器人的配置信息
        # Parse bot configuration and get default collections once
        bot_config = None
        default_collections = []
        custom_system_prompt = None
        custom_query_prompt = None
        # 解析机器人的流程配置
        if bot.config:
            try:
                config_dict = json.loads(bot.config)  # bot.config 是数据库中存储的 JSON 字符串，包含 Agent 专属配置
                if config_dict:
                    bot_config = view_models.BotConfig(**config_dict)  # 将bot.config转化为BotConfig实例【内含agent和flow属性】
            except (json.JSONDecodeError, ValueError):
                bot_config = None

        if bot_config and bot_config.agent:  # 如果bot配置中的agent配置项非空，则获取其中的提示词、知识库信息
            # Get custom prompts from bot config
            custom_system_prompt = bot_config.agent.system_prompt_template
            custom_query_prompt = bot_config.agent.query_prompt_template

            # Get default collections once for performance
            if bot_config.agent.collections:
                collection_ids = [collection.id for collection in bot_config.agent.collections]
                db_collections = await self.db_ops.query_collections_by_ids(user, collection_ids)
                # Convert SQLAlchemy models to Pydantic models
                default_collections = await self._convert_db_collections_to_pydantic(db_collections)  # 知识库信息的格式封装【转换为view_models.Collection实例】
        # -- 核心循环：持续接收前端消息并处理【在此之前的逻辑主要用于获取当前机器人的配置上下文】
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_text()  # 接收前端消息

            # Parse WebSocket message using Go-style error handling
            agent_message, error_response = self._parse_websocket_message(data)  # 将前端消息转化为view_models.AgentMessage实例
            if error_response:  # 解析前端消息时触发异常，直接通过websocket返回前端异常信息
                await websocket.send_text(json.dumps(error_response))
                continue

            # Process each message in a new trace context
            await self._handle_single_message(
                websocket,  # websocket连接，用以适时推送消息
                agent_message,  # 前端数据的格式化封装【view_models.AgentMessage实例】
                user,
                bot,  # 机器人信息
                chat_id,  # 对话窗口id
                bot_config=bot_config,  # 机器人配置信息
                default_collections=default_collections,  # 机器人配置中的知识库信息列表
                # 机器人配置中的提示词
                custom_system_prompt=custom_system_prompt,
                custom_query_prompt=custom_query_prompt,
            )  # 处理单个消息的回答

    """
    @trace_async_function 装饰器：用于 “链路追踪”，为每个消息处理创建独立的追踪 ID（trace_id），便于日志记录和问题排查（如追踪一个用户提问从接收→处理→推送的完整链路）。
    new_trace=True 表示每个消息都启用新的追踪上下文。
    """
    @trace_async_function("name=handle_single_websocket_message", new_trace=True)
    async def _handle_single_message(
        self,
        websocket: WebSocket,
        agent_message: view_models.AgentMessage,  # 前端数据的格式化封装【view_models.AgentMessage实例】
        user: str,
        bot: any,
        chat_id: str,
        bot_config=None,
        default_collections=None,
        custom_system_prompt=None,
        custom_query_prompt=None,
    ):  # 处理单个WebSocket消息的回答【根据其历史对话记录回答当前问题，基于chat_id从redis中获取】
        """
        核心设计思想：生产者-消费者模型
            - 解耦处理与推送：Agent 处理逻辑（可能耗时，如调用多个工具）和前端推送逻辑分离，避免处理耗时阻塞实时推送。
            - 支持流式反馈：Agent 生成的中间结果（如 “正在调用工具”“部分回答”）可通过队列实时推送给前端，用户体验更流畅。
            - 容错性提升：单个任务失败（如推送失败）不影响另一个任务（如处理仍可完成），便于单独重试或修复。
        """
        """
        完整流程：
            - 初始化消息 ID 和队列，注册链路追踪；
            - 关联用户上传的文件（若有）；
            - 启动并行任务：
                - 生产者（process_task）：处理提问，生成回答和中间结果，放入队列；
                - 消费者（consumer_task）：从队列取结果，实时推送给前端；
            - 处理任务异常，推送错误提示（若失败）；
            - 保存对话历史（若成功）；
            - 清理资源，注销监听器。

        """
        """处理单个用户提问（通过 WebSocket 接收的 agent_message），协调 “消息处理” 和 “结果推送” 两个异步任务，最终完成回答生成、历史保存等闭环操作。"""
        """Handle a single WebSocket message with its own trace"""
        trace_id = None
        try:
            message_id = str(uuid.uuid4())  # 生成当前消息的唯一标识
            message_queue = AgentMessageQueue()  # 初始化异步消息队列【用于代理聊天通信的异步消息队列。Agent内部通信的载体】
            trace_id = await self.register_message_queue(agent_message.language, chat_id, message_id, message_queue)  # 注册消息队列，返回追踪ID（用于关联整个消息处理链路）

            # Get document metadata and associate documents with message if files are provided
            from aperag.service.chat_document_service import chat_document_service
            # 将用户上传的文件与当前消息绑定（文件ID列表来自agent_message.files）【将文件 ID 与当前 message_id 绑定，后续处理时可直接获取这些文件的内容（如作为 Agent 调用工具的输入）】
            files = await chat_document_service.associate_documents_with_message(
                chat_id=chat_id, message_id=message_id, files=[file.id for file in agent_message.files], user=user
            )
            # 生产者任务：处理消息（调用Agent逻辑生成回答、工具调用等）
            # Message Producer: Start background task to process agent generation message
            process_task = asyncio.create_task(
                self.process_agent_message(
                    agent_message,
                    user,
                    bot,
                    chat_id,
                    message_id,
                    message_queue,  # 消息队列（用于向消费者推送中间结果）
                    bot_config=bot_config,
                    default_collections=default_collections,
                    custom_system_prompt=custom_system_prompt,
                    custom_query_prompt=custom_query_prompt,
                )
            )  # 调用 Agent 处理用户提问（如解析问题、调用工具、生成回答），将中间结果（如 “正在调用搜索工具”“回答片段”）放入 message_queue。

            # 消费者任务：从消息队列取数据，实时推送给前端
            # Message Consumer
            consumer_task = asyncio.create_task(
                self._consume_messages_from_queue(chat_id, message_id, trace_id,
                                                  message_queue,   # 消息队列（从这里获取生产者的输出）
                                                  websocket)
            )  # 持续监听 message_queue，一旦有新数据（如 Agent 生成的回答片段、工具调用状态），立即通过 WebSocket 推送给前端，实现 “实时反馈”（如显示 “Agent 正在调用计算器”“回答片段”）。
            # 等待两个任务完成（支持异常捕获）【两个任务并行执行，提高效率；return_exceptions=True 确保单个任务出错时，另一个任务的结果仍能被捕获，便于统一处理错误。】
            process_result, consumer_result = await asyncio.gather(process_task, consumer_task, return_exceptions=True)
            # 异常处理确保单个任务失败不会导致整个 WebSocket 连接崩溃，符合 “健壮性设计”。
            # 处理生产者任务异常【若生产者（process_task）失败（如 Agent 调用工具出错），生成错误响应并通过 WebSocket 推送给前端，告知用户 “处理失败”。】
            # Handle process_task exceptions with unified error formatting
            if isinstance(process_result, Exception):
                logger.error(f"Process task failed: {process_result}")
                error_response = self._format_exception_to_error_response(
                    process_result, agent_message.language or "en-US"
                )
                await websocket.send_text(json.dumps(error_response))
                return
            # 处理消费者任务异常【若消费者（consumer_task）失败（如推送消息时连接中断），同样记录错误并推送提示。】
            # Handle consumer_task exceptions
            if isinstance(consumer_result, Exception):
                logger.error(f"Consumer task failed: {consumer_result}")
                error_response = format_processing_error(str(consumer_result), agent_message.language or "en-US")
                await websocket.send_text(json.dumps(error_response))
                return
            # 从生产者结果中提取关键信息
            # Handle history saving at WebSocket layer (better separation of concerns)
            # process_result now contains {query, content, references} on success
            query = process_result.get("query", "")
            ai_response = process_result.get("content", "")  # Agent最终回答
            references = process_result.get("references", "")  # 参考资料
            tool_use_list = consumer_result  # 消费者返回的工具调用记录
            # 保存对话历史到数据库/Redis
            await self._save_conversation_history(
                chat_id, message_id, trace_id,
                query, ai_response, files,  # 用户提问、AI回答、关联文件
                tool_use_list, references  # 工具调用记录、参考资料
            )

        except Exception as e:
            # This catches any other unexpected errors not handled above
            logger.error(f"Unexpected error processing agent websocket message: {e}")
            error_response = format_processing_error(str(e), agent_message.language or "en-US")
            await websocket.send_text(json.dumps(error_response))
        finally:
            if trace_id:
                # 注销该trace_id的监听器（释放资源）【无论处理成功或失败，最终都会注销 trace_id 对应的监听器，避免资源泄露（如持续占用内存监听已完成的任务）。】
                await agent_event_listener.unregister_listener(str(trace_id))

    async def register_message_queue(self, language, chat_id, message_id, message_queue):
        # Get the trace_id from the current span
        from aperag.trace.mcp_integration import get_current_trace_info

        trace_id, _ = get_current_trace_info()  # 从当前追踪上下文获取trace_id（链路唯一标识）
        if not trace_id:  # 若获取不到trace_id，记录错误（可能影响后续事件追踪）
            logger.error("Could not get trace_id from current span, event dispatching will fail.")
        else:
            # Register a listener for this request with the global proxy.
            await agent_event_listener.register_listener(
                trace_id=str(trace_id),
                chat_id=chat_id,
                message_id=message_id,
                queue=message_queue,
                language=language,
            )   # 将trace_id与当前对话、消息、队列绑定，注册到全局监听器。【实现 “链路标识” 与 “业务数据” 的关联】
        return trace_id

    async def _stream_message_content(
        self, message: Dict[str, Any], websocket: WebSocket, chunk_size: int = 5, delay: float = 0.01
    ) -> None:
        """
        Stream message content in small chunks to simulate typing effect.

        Args:
            message: The message dict with type="message"
            websocket: WebSocket connection to send chunks
            chunk_size: Number of characters per chunk
            delay: Delay in seconds between chunks
        """
        content = message.get("data", "")
        if not content:
            # If no content, send the original message
            await websocket.send_text(json.dumps(message))
            return

        # Split content into chunks
        chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]

        for i, chunk in enumerate(chunks):
            # Create a chunk message with same structure but partial content
            chunk_message = {
                "type": "message",
                "id": message.get("id"),
                "data": chunk,
                "timestamp": message.get("timestamp", int(time.time())),
            }

            await websocket.send_text(json.dumps(chunk_message))
            logger.debug(f"Sent message chunk {i + 1}/{len(chunks)}: {len(chunk)} chars")

            # Add delay between chunks (except for the last one)
            if i < len(chunks) - 1:
                await asyncio.sleep(delay)

    async def _consume_messages_from_queue(
        self, chat_id: str, message_id: str, trace_id: str, message_queue: AgentMessageQueue, websocket: WebSocket
    ) -> List[AgentToolCallResultResponse]:
        """
        Consume messages from queue, send to WebSocket, and collect AgentToolCallResultResponse messages.

        This method runs as a separate task to avoid race conditions.
        Returns a list of all AgentToolCallResultResponse messages.
        """
        try:
            # Properly initialize list to collect AgentToolCallResultResponse messages
            tool_call_results: List[Dict] = []

            while True:
                # Get message from queue (blocks until message is available)
                message = await message_queue.get()

                # None message signals end of stream
                if message is None:
                    logger.debug("Received end-of-stream signal from message queue")
                    break

                # Collect AgentToolCallResultResponse messages
                if isinstance(message, dict) and message.get("type") == "tool_call_result":
                    tool_call_results.append(message)

                # Special handling for type="message" - stream it in chunks
                if isinstance(message, dict) and message.get("type") == "message":
                    await self._stream_message_content(message, websocket)
                    logger.debug(f"Streamed message content: {message.get('type', 'unknown')}")
                else:
                    # Send other message types normally (start, stop, tool_call_result, etc.)
                    await websocket.send_text(json.dumps(message))
                    logger.debug(f"Sent message to WebSocket: {message.get('type', 'unknown')}")

            return tool_call_results

        except Exception as e:
            logger.error(f"Error in message consumer: {e}")
            raise

    async def _get_agent_session(
        self, agent_message: view_models.AgentMessage, user: str, chat_id: str, custom_system_prompt: str = None
    ):
        """Get or create chat session using AgentConfig."""
        # Query provider details and API key from database
        provider_info = await self.db_ops.query_llm_provider_by_name(agent_message.completion.model_service_provider)
        if not provider_info:
            error_msg = f"Provider '{agent_message.completion.model_service_provider}' not found in database"
            logger.error(error_msg)
            raise AgentConfigurationError(error_msg)

        api_key = await self.db_ops.query_provider_api_key(
            agent_message.completion.model_service_provider, user_id=user, need_public=True
        )
        if not api_key:
            error_msg = f"No API key available for provider '{agent_message.completion.model_service_provider}'"
            logger.error(error_msg)
            raise AgentConfigurationError(error_msg)

        aperag_api_keys = await self.db_ops.query_api_keys(user, is_system=True)
        for item in aperag_api_keys:
            aperag_api_key = item.key
        if not aperag_api_key:
            # Auto-create a new system aperag API key for the user if none exists
            logger.info(f"No aperag API key found for user {user}, creating a new system key")
            try:
                api_key_result = await self.db_ops.create_api_key(user=user, description="aperag", is_system=True)
                aperag_api_key = api_key_result.key
                logger.info(f"Successfully created new system aperag API key for user {user}")
            except Exception as e:
                error_msg = f"Failed to create aperag API key for user {user}: {str(e)}"
                logger.error(error_msg)
                raise AgentConfigurationError(error_msg)

        # Determine system prompt: use custom if provided, otherwise use default
        system_prompt = (
            custom_system_prompt if custom_system_prompt else get_agent_system_prompt(language=agent_message.language)
        )

        # Create AgentConfig with all needed parameters including chat_id
        config = AgentConfig(
            user_id=user,
            chat_id=chat_id,
            provider_name=agent_message.completion.model_service_provider,
            api_key=api_key,
            base_url=provider_info.base_url,
            default_model=agent_message.completion.model,
            language=agent_message.language if agent_message.language else "en-US",
            instruction=system_prompt,
            server_names=["aperag"],
            aperag_api_key=aperag_api_key,
            aperag_mcp_url=os.getenv("APERAG_MCP_URL", "http://localhost:8000/mcp/"),
            temperature=0.7,
            max_tokens=60000,
        )

        # Get or create chat session using config
        session = await agent_session_manager.get_or_create_session(config)

        return session

    async def process_agent_message(
        self,
        agent_message: view_models.AgentMessage,
        user: str,
        bot: any,
        chat_id: str,
        message_id: str,
        message_queue: AgentMessageQueue,
        bot_config=None,
        default_collections=None,
        custom_system_prompt=None,
        custom_query_prompt=None,
    ) -> Dict[str, Any]:
        # Use pre-parsed configuration for performance
        # Priority: agent_message > bot_config > defaults
        final_completion = agent_message.completion
        final_collections = agent_message.collections

        # Use bot config as fallback for completion and collections
        if not final_completion and bot_config and bot_config.agent and bot_config.agent.completion:
            final_completion = bot_config.agent.completion

        if not final_collections and default_collections:
            final_collections = default_collections

        # Validate ModelSpec
        if not final_completion or not final_completion.model:
            raise AgentConfigurationError(
                config_key="completion.model", reason="Model specification is required for AI response generation"
            )

        # Create a new agent message with merged configuration
        merged_agent_message = view_models.AgentMessage(
            query=agent_message.query,
            collections=final_collections,
            completion=final_completion,
            web_search_enabled=agent_message.web_search_enabled,
            language=agent_message.language,
            files=agent_message.files,
        )

        try:
            # Send start message
            await message_queue.put(format_stream_start(message_id))

            # Create memory from chat history
            history = await self.history_manager.get_chat_history(chat_id)
            memory = await self.memory_manager.create_memory_from_history(history, context_limit=4)

            # Get chat session using merged agent message and custom system prompt
            session = await self._get_agent_session(merged_agent_message, user, chat_id, custom_system_prompt)
            llm = await session.get_llm(final_completion.model)

            llm.history = memory

            # Build query prompt using custom template if provided
            comprehensive_prompt = build_agent_query_prompt(
                chat_id, agent_message=merged_agent_message, user=user, custom_template=custom_query_prompt
            )

            request_params = RequestParams(
                maxTokens=8192,
                model=final_completion.model,
                use_history=True,
                max_iterations=10,
                parallel_tool_calls=True,
                temperature=0.7,
                user=user,
            )
            response = await llm.generate_str(comprehensive_prompt, request_params)
            full_content = response if response else "No response generated"

            await asyncio.sleep(0.1)  # Allow time for the message to be processed in listener

            await message_queue.put(format_stream_content(message_id, full_content))

            tool_references = extract_tool_call_references(llm.history)
            urls = []

            await message_queue.put(format_stream_end(message_id, references=tool_references, urls=urls))

            return {
                "query": merged_agent_message.query,
                "content": full_content,
                "references": tool_references,
            }

        finally:
            await message_queue.close()

    def _format_exception_to_error_response(self, exception: Exception, language: str) -> AgentErrorResponse:
        """
        Convert exception to properly formatted error response using unified error handling.

        Args:
            exception: The exception to format
            language: Language code for i18n error messages

        Returns:
            Formatted error response for WebSocket
        """
        # Use existing exception hierarchy and formatting utilities
        if isinstance(exception, AgentConfigurationError):
            # Check for specific configuration error types
            error_msg = str(exception).lower()
            if "model" in error_msg or "completion" in error_msg:
                return format_invalid_model_spec_error(str(exception), language)
            else:
                return format_agent_setup_error(str(exception), language)

        elif isinstance(exception, MCPConnectionError):
            return format_mcp_connection_error(language)

        elif isinstance(exception, MCPAppInitializationError):
            return format_agent_setup_error(str(exception), language)

        else:
            # Handle unexpected errors with generic processing error
            return format_processing_error(str(exception), language)

    async def chat_for_evaluation(
        self,
        query: str,
        user_id: str,
        model_name: str,
        model_service_provider: str,
        custom_llm_provider: Optional[Dict],
        collections: List[view_models.Collection],
        language: str = "en-US",
    ) -> StoredChatMessage | AgentErrorResponse:
        """
        Handle internal chat requests for evaluation tasks, bypassing WebSockets.
        Returns the AI response as a dictionary representation of StoredChatMessage.
        """
        # Construct AgentMessage
        agent_message = view_models.AgentMessage(
            query=query,
            completion=view_models.ModelSpec(
                model=model_name,
                model_service_provider=model_service_provider,
                custom_llm_provider=custom_llm_provider,
            ),
            collections=collections,
            language=language,
        )

        # Generate unique IDs for this interaction
        chat_id = f"eval-chat-{uuid.uuid4()}"
        message_id = str(uuid.uuid4())
        trace_id = None

        try:
            message_queue = AgentMessageQueue()
            trace_id = await self.register_message_queue(agent_message.language, chat_id, message_id, message_queue)

            # Simplified consumer that just collects results without a websocket
            async def consume_and_collect():
                tool_calls = []
                while True:
                    message = await message_queue.get()
                    if message is None:
                        break
                    if isinstance(message, dict) and message.get("type") == "tool_call_result":
                        tool_calls.append(message)
                return tool_calls

            process_task = asyncio.create_task(
                self.process_agent_message(agent_message, user_id, chat_id, message_id, message_queue)
            )
            consumer_task = asyncio.create_task(consume_and_collect())

            process_result, consumer_result = await asyncio.gather(process_task, consumer_task, return_exceptions=True)

            # Handle process_task exceptions with unified error formatting
            if isinstance(process_result, Exception):
                logger.error(f"Process task failed: {process_result}")
                error_response = self._format_exception_to_error_response(
                    process_result, agent_message.language or "en-US"
                )
                return error_response

            # Handle consumer_task exceptions
            if isinstance(consumer_result, Exception):
                logger.error(f"Consumer task failed: {consumer_result}")
                error_response = format_processing_error(str(consumer_result), agent_message.language or "en-US")
                return error_response

            query = process_result.get("query", "")
            ai_response = process_result.get("content", "")
            references = process_result.get("references", "")
            tool_use_list = consumer_result

            # AI message
            ai_message = create_assistant_message(
                content=ai_response,
                chat_id=chat_id,
                message_id=message_id,
                trace_id=trace_id,
                tool_use_list=tool_use_list,
                references=references,
                # urls=,
            )
            return ai_message

        except Exception as e:
            logger.error(f"Error during internal agent chat for evaluation: {e}")
            error_response = self._format_exception_to_error_response(e, agent_message.language or "en-US")
            return error_response
        finally:
            if trace_id:
                await agent_event_listener.unregister_listener(str(trace_id))

    async def _save_conversation_history(
        self,
        chat_id: str,
        message_id: str,
        trace_id: str,
        query: str,
        ai_response: str,
        files: List[Dict[str, Any]],
        tool_use_list: List[Dict],
        tool_references: List[Dict[str, Any]],
    ) -> None:
        """
        Save conversation history from successful agent processing.

        Args:
            chat_id: Chat session ID
            conversation_data: Dictionary containing query, content, and references
        """
        try:
            # Get history instance through history manager
            history = await self.history_manager.get_chat_history(chat_id)

            # Save conversation turn with data from successful processing
            history_saved = await self.history_manager.save_conversation_turn(
                message_id=message_id,
                trace_id=trace_id,
                history=history,
                user_query=query,
                ai_response=ai_response,
                files=files,
                tool_use_list=tool_use_list,
                tool_references=tool_references,
            )

            if not history_saved:
                logger.warning(f"Failed to save conversation history for chat: {chat_id}")

        except Exception as e:
            # Don't let history saving errors break the flow
            logger.error(f"Error saving conversation history for chat {chat_id}: {e}")
