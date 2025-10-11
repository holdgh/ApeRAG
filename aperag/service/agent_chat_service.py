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
        """
        处理单个用户提问（通过 WebSocket 接收的 agent_message），协调 “消息处理” 和 “结果推送” 两个异步任务，最终完成回答生成、历史保存等闭环操作。"""
        """
        这段逻辑的完整闭环如下：
            - 注册监听器：_handle_single_message 调用 register_listener，为当前提问创建专属的 AgentEventProcessor，并绑定消息队列；
            - Agent 调用工具：process_agent_message（生产者任务）中，Agent 调用工具（如搜索），系统生成 “工具调用结果事件”（event.message = "send_request: response="）；
            - 事件捕获与处理：AgentEventProcessor 的 handle_event 捕获事件，通过 _handle_tool_response 处理结果并写入消息队列；
            - 前端推送：_consume_messages_from_queue（消费者任务）从消息队列中读取工具结果，通过 WebSocket 推送给前端；
            - 用户看到结果：前端显示 “Agent 调用工具的结果”（如 “【搜索结果】根据知识库，RAG 的核心是...）。
    
        核心设计价值：
            - 解耦工具调用与结果推送：
            Agent 调用工具的逻辑（生产者）与结果推送逻辑（消费者）通过 “事件 + 消息队列” 解耦，Agent 无需关心结果如何推送，只需生成事件即可；
            - 精准匹配链路：
            通过 trace_id 确保 “工具结果” 只匹配 “当前提问的链路”，避免多用户、多对话场景下的数据混淆；
            - 灵活的结果处理：
            通过 ToolResultFormatter 封装结果解析和格式化逻辑，支持新增工具类型（如 “表格生成工具”）时，只需扩展 formatter 即可，无需修改核心流程；
            - 容错性强：
            多层异常捕获（@handle_agent_error、数据校验）确保工具结果处理失败时，不影响整个对话流程，只跳过当前结果。
        """
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
        """
        一、链路追踪的核心作用
            链路追踪（Tracing）是分布式系统中用于监控和诊断请求处理流程的关键技术，在这个 RAG/Agent 系统中，其作用具体体现为：
            1. 全链路可视化：追踪单个对话的完整处理路径
            一个用户提问在系统中的处理可能涉及多个步骤（如：接收请求→解析消息→调用知识库→调用 LLM→调用工具→生成回答→推送结果），trace_id 作为唯一标识，将这些步骤串联成一个完整的 “链路”，通过可视化工具（如 Jaeger、Zipkin）可直观看到：
                - 每个步骤的执行顺序、耗时；
                - 步骤之间的调用关系（如 “调用 LLM” 依赖 “知识库检索” 的结果）。    
            例如：通过追踪 trace_id=abc123，可清晰看到 “用户提问‘如何调优 RAG’” 的处理路径：
            接收消息（0.1s）→ 检索知识库（1.2s）→ 调用LLM（3.5s）→ 推送回答（0.05s）。
            2. 问题排查与性能优化：定位瓶颈和错误点
                - 错误定位：当对话处理失败时（如回答为空、工具调用超时），可通过 trace_id 检索所有相关日志，快速定位哪个步骤出错（如 “工具调用时 API 超时”）；
                - 性能分析：通过各步骤的耗时统计，发现系统瓶颈（如 “知识库检索耗时过长”），针对性优化（如增加缓存、优化索引）；
                - 依赖分析：识别系统中哪些组件（如 LLM 服务、工具 API）是性能瓶颈或错误高发区，指导资源投入。   
            3. 业务可观测性：理解系统行为与用户交互    
                - 可统计不同类型对话的处理链路特征（如 “含文件上传的对话” 比 “纯文本对话” 多哪些步骤）；
                - 分析 Agent 的工具调用链路（如 “调用搜索工具” 后是否常跟随 “调用计算器”），优化 Agent 的决策逻辑；
                - 结合 chat_id 和 message_id，将追踪数据与业务数据（如用户 ID、机器人类型）关联，实现 “技术指标 + 业务指标” 的联合分析。      
            4. 分布式系统的协同诊断
            在微服务架构中（如 Agent 服务、知识库服务、LLM 服务独立部署），一个对话请求可能跨多个服务：
                - 链路追踪通过 trace_id 在不同服务间传递，确保跨服务的调用可被完整追踪；
                - 避免了传统日志分散在多个服务中、难以关联的问题（如 “Agent 服务调用知识库服务超时”，通过 trace_id 可同时查看两个服务的相关日志）。 
        二、与 “工作流” 的区别与联系
            区别在于：          
                工作流（Workflow）：定义 “任务执行的流程规则”（如 “先检索再调用 LLM”），是业务逻辑的设计；
                链路追踪（Tracing）：不改变业务流程，而是记录流程的实际执行情况（如 “检索用了多久”“LLM 调用是否成功”），是监控和诊断工具。    
            联系在于：链路追踪可以 “记录工作流的实际执行过程”，帮助验证工作流是否按预期运行，或优化工作流的步骤设计。
        三、总结
            这段代码通过 OpenTelemetry 实现了分布式链路追踪的核心功能：
                - 生成并传递 trace_id，作为单个对话请求的全局唯一标识；
                - 将 trace_id 与业务数据（chat_id、message_id）绑定，实现 “技术追踪” 与 “业务上下文” 的关联；
                - 最终通过追踪数据实现全链路可视化、问题排查、性能优化和业务分析。
            链路追踪是保障复杂系统（尤其是分布式架构）稳定性和可维护性的关键技术，在 Agent 这类涉及多步骤、多工具调用的系统中尤为重要。
        """
        trace_id, _ = get_current_trace_info()  # 从当前追踪上下文获取trace_id（链路唯一标识）【对应一次用户问答交互流程】
        if not trace_id:  # 若获取不到trace_id，记录错误（可能影响后续事件追踪）
            logger.error("Could not get trace_id from current span, event dispatching will fail.")
        else:  # 若 trace_id 存在
            # Register a listener for this request with the global proxy.
            """
            Agent 系统中 “事件监听与工具响应处理” 的核心实现，负责将 Agent 调用工具的结果（如搜索结果、计算结果）通过 “事件机制” 捕获并转发到消息队列，最终推送给前端。
            """
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
    ):  # 基于agent配置【内含：用户、对话窗口id、模型信息【提供商、api_key、base_url、模型名称】、语言参数、系统提示词、用户的aperag_api_key、本地mcp服务接口等】获取聊天会话
        """Get or create chat session using AgentConfig."""
        # -- 获取模型供应商信息及相应的api_key
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
        # -- 获取用户的ape_api_key【用以调用本地mcp服务】，如果不存在，则创建
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
        # -- 获取系统提示词
        # Determine system prompt: use custom if provided, otherwise use default
        system_prompt = (
            custom_system_prompt if custom_system_prompt else get_agent_system_prompt(language=agent_message.language)
        )  # 默认机器人配置中没有任何数据，也就没有custom_system_prompt，这里采用了get_agent_system_prompt(language=agent_message.language)获取系统提示词
        # -- 基于用户、对话窗口id、模型信息【提供商、api_key、base_url、模型名称】、语言参数、系统提示词、用户的aperag_api_key【用以调用本地mcp服务】、本地mcp服务接口等初始化agent配置
        # Create AgentConfig with all needed parameters including chat_id
        config = AgentConfig(
            user_id=user,
            chat_id=chat_id,
            provider_name=agent_message.completion.model_service_provider,
            api_key=api_key,
            base_url=provider_info.base_url,
            default_model=agent_message.completion.model,
            language=agent_message.language if agent_message.language else "en-US",
            instruction=system_prompt,  # 系统提示词
            server_names=["aperag"],  # mcp服务名称
            aperag_api_key=aperag_api_key,
            aperag_mcp_url=os.getenv("APERAG_MCP_URL", "http://localhost:8000/mcp/"),
            temperature=0.7,
            max_tokens=60000,
        )
        # -- 基于agent配置创建聊天会话
        # Get or create chat session using config
        session = await agent_session_manager.get_or_create_session(config)

        return session

    async def process_agent_message(
        self,
        agent_message: view_models.AgentMessage,  # 前端用户消息
        user: str,
        bot: any,
        chat_id: str,  # 对话窗口id
        message_id: str,  # 前端用户消息id
        message_queue: AgentMessageQueue,  # 消息队列（用于传递工具结果）
        # 机器人关于对话的配置信息【知识库、提示词等】
        bot_config=None,
        default_collections=None,
        custom_system_prompt=None,
        custom_query_prompt=None,
    ) -> Dict[str, Any]:  # 处理消息（调用Agent逻辑生成回答、工具调用等）TODO rag在哪里实现的？
        # -- 解析问答相关配置【优先级：用户选择>机器人配置>默认选项】
        # Use pre-parsed configuration for performance
        # Priority: agent_message > bot_config > defaults
        final_completion = agent_message.completion  # 用户选择的模型
        final_collections = agent_message.collections  # 用户选择的知识库列表
        # 根据优先级，确定所用知识库和模型
        # Use bot config as fallback for completion and collections
        if not final_completion and bot_config and bot_config.agent and bot_config.agent.completion:
            final_completion = bot_config.agent.completion

        if not final_collections and default_collections:
            final_collections = default_collections
        # 校验模型信息
        # Validate ModelSpec
        if not final_completion or not final_completion.model:
            raise AgentConfigurationError(
                config_key="completion.model", reason="Model specification is required for AI response generation"
            )
        # -- 根据最终配置，重构前端消息
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
            # -- 向队列发送开始消息，标识事件开始
            # Send start message
            await message_queue.put(format_stream_start(message_id))
            # -- 根据对话窗口id从redis获取对话历史信息并创建对话历史上下文内存
            # Create memory from chat history
            history = await self.history_manager.get_chat_history(chat_id)
            memory = await self.memory_manager.create_memory_from_history(history, context_limit=4)
            # -- 基于用户、对话窗口id、模型信息【提供商、api_key、base_url、模型名称】、语言参数、系统提示词、用户的aperag_api_key、本地mcp服务接口等【封装为agent配置】获取聊天会话
            # Get chat session using merged agent message and custom system prompt
            session = await self._get_agent_session(merged_agent_message, user, chat_id, custom_system_prompt)
            # -- 获取聊天会话中的llm并为其设置对话历史
            llm = await session.get_llm(final_completion.model)

            llm.history = memory
            # -- 构建给到llm的最终提示词【并非回答提示词，而是一种动态逻辑提示词，让llm自主根据逻辑说明规划回答流程，并采用工具调用的方式完成相应逻辑节点】
            # Build query prompt using custom template if provided
            comprehensive_prompt = build_agent_query_prompt(
                chat_id, agent_message=merged_agent_message, user=user, custom_template=custom_query_prompt
            )
            # -- 构造llm请求参数并基于最终提示词使用llm生成响应
            request_params = RequestParams(
                maxTokens=8192,
                model=final_completion.model,
                use_history=True,
                max_iterations=10,
                parallel_tool_calls=True,
                temperature=0.7,
                user=user,
            )
            """
            工具调用的隐式逻辑（核心！回答 “RAG 在哪里实现”）：
                代码中没有显式的 “RAG 检索” 代码，是因为 “检索逻辑被 LLM 驱动的工具调用隐式执行”，具体流程如下：
                1、LLM 生成工具调用指令：
                    LLM 解析提示词后，若判断需要检索知识库，会生成符合格式的 “工具调用指令”（如 JSON 格式）：
                        {"tool": "knowledge_search", "params": {"collection_ids": ["col123"], "query": "如何配置 RAG 知识库"}}
                
                2、MCP 服务执行工具调用：
                    ChatSession 中的 mcp_app（MCP 服务）会监听 LLM 输出的工具指令，调用对应的 “知识库检索工具”（内部实现向量数据库查询、文档过滤、相关片段提取）；
                3、工具结果回传 Agent：
                    检索结果通过之前的 message_queue（消息队列）回传，AgentEventProcessor（事件监听器）捕获结果后，格式化并写入队列；
                4、LLM 整合结果继续决策：
                    Agent 将工具结果再次传入 LLM，LLM 判断 “结果是否足够”—— 若足够则生成回答，若不足则继续调用其他工具（如网络搜索）；
                5、最终生成回答：
                    当 LLM 判断信息足够时，生成符合提示词要求的自然语言回答（包含来源标注、区分用户指定 / 额外来源）。
            """
            """
            1、能力注入 —— 提示词告知 LLM “如何使用 MCP 工具”
            LLM 之所以知道 “何时调用 MCP 工具、调用哪个工具”，核心是 提示词中包含了 “工具使用指南”，
            这些指南通过 custom_system_prompt（系统提示词）和 comprehensive_prompt（综合提示词）传递给 LLM，完成 “能力注入”。
            
            2、当 LLM 根据提示词决定调用工具时，不会直接与 MCP 交互，而是通过 Agent 作为 “中间翻译官”，完成 “LLM 自然语言指令 → Agent 结构化指令 → MCP 工具调用” 的转化：
            具体流程（隐式逻辑，基于代码推导）：
            - LLM 生成工具调用意图：
            LLM 解析综合提示词后，生成包含 “工具调用意图” 的文本，例如：
                “我需要调用知识库检索工具，查询用户指定的‘产品文档库’（ID: col123），关键词是‘如何配置 RAG 知识库’。”
            - Agent 解析意图为结构化指令：
            Agent内置 “工具调用解析逻辑”，将 LLM 的自然语言意图转化为 MCP 能理解的结构化指令（如 JSON）：
                {"tool": "knowledge_search", "params": {"collection_ids": ["col123"], "query": "如何配置 RAG 知识库", "session_id": "chat456"}}
                其中 session_id 来自self._get_agent_session生成的会话，确保 MCP 能将结果返回给当前会话。
            - Agent 向 MCP 发送指令：
                Agent 通过 session.mcp_running_app（会话session运行中的 MCP 实例，见aperag.agent.agent_session_manager.ChatSession.initialize和aperag.agent.mcp_app_factory.MCPAppFactory.create_mcp_app）提供的接口，将结构化指令发送给对应的 MCP 工具：
                    MCP 收到指令后，找到名为 knowledge_search 的工具；
                    执行工具内部逻辑（如查询向量数据库、过滤相关文档、提取关键片段）；
                    生成工具调用结果（如包含 “RAG 配置步骤” 的文档片段列表）。

            3、结果反馈 ——MCP 工具结果通过 Agent 回传给 LLM
            Agent 拿到 MCP 的原始结果后，会按照提示词要求（如 “标注来源”“区分用户指定知识库”）进行初步格式化，然后将其写入 LLM 的 history（上下文内存）：
                # 伪代码：Agent 将 MCP 结果注入 LLM 上下文
                formatted_tool_result = f"【知识库来源：产品文档库（ID: col123）】\n检索结果：{mcp_tool_result['fragments'][0]['content']}"
                # 写入 LLM 的 history，供后续决策使用
                self.llm.history.add_message(role="system", content=formatted_tool_result)
            此时 LLM 能从 history 中读取到工具结果，进而判断 “是否需要继续调用其他工具” 或 “可以生成最终回答”。

            4、总结：ChatSession 中 LLM 与 MCP 工具的联系，本质是 “提示词驱动决策，Agent 协调交互，MCP 执行操作” 的分工协作模式：
            """
            # 系统提示词
            response = await llm.generate_str(comprehensive_prompt, request_params)
            full_content = response if response else "No response generated"

            await asyncio.sleep(0.1)  # Allow time for the message to be processed in listener
            # -- 将模型响应存入消息队列
            await message_queue.put(format_stream_content(message_id, full_content))
            # -- 提取对话历史中的工具调用并存入消息队列
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
