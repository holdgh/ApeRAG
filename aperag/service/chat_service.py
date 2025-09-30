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

import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from aperag.db import models as db_models
from aperag.db.ops import AsyncDatabaseOps, async_db_ops
from aperag.exceptions import ChatNotFoundException, ResourceNotFoundException
from aperag.flow.engine import FlowEngine
from aperag.flow.parser import FlowParser
from aperag.schema import view_models
from aperag.schema.view_models import Chat, ChatDetails
from aperag.utils.constant import DOC_QA_REFERENCES, DOCUMENT_URLS
from aperag.utils.history import (
    RedisChatMessageHistory,
    fail_response,
    get_async_redis_client,
    references_response,
    start_response,
    stop_response,
    success_response,
)

logger = logging.getLogger(__name__)


class FrontendFormatter:
    """Format responses according to Aperag custom format"""

    @staticmethod
    def format_stream_start(msg_id: str) -> Dict[str, Any]:
        """Format the start event for streaming"""
        return {
            "type": "start",
            "id": msg_id,
            "timestamp": int(time.time()),
        }

    @staticmethod
    def format_stream_content(msg_id: str, content: str) -> Dict[str, Any]:
        """Format a content chunk for streaming"""
        return {
            "type": "message",
            "id": msg_id,
            "data": content,
            "timestamp": int(time.time()),
        }

    @staticmethod
    def format_stream_end(
        msg_id: str,
        references: List[str] = None,
        memory_count: int = 0,
        urls: List[str] = None,
    ) -> Dict[str, Any]:
        """Format the end event for streaming"""
        if references is None:
            references = []
        if urls is None:
            urls = []

        return {
            "type": "stop",
            "id": msg_id,
            "data": references,
            "memoryCount": memory_count,
            "urls": urls,
            "timestamp": int(time.time()),
        }

    @staticmethod
    def format_complete_response(msg_id: str, content: str) -> Dict[str, Any]:
        """Format a complete response for non-streaming mode"""
        return {
            "type": "message",
            "id": msg_id,
            "data": content,
            "timestamp": int(time.time()),
        }

    @staticmethod
    def format_error(error: str) -> Dict[str, Any]:
        """Format an error response"""
        return {
            "type": "error",
            "id": str(uuid.uuid4()),
            "data": error,
            "timestamp": int(time.time()),
        }


class ChatService:
    """Chat service that handles business logic for chats"""

    def __init__(self, session: AsyncSession = None):
        # Use global db_ops instance by default, or create custom one with provided session
        if session is None:
            self.db_ops = async_db_ops  # Use global instance
        else:
            self.db_ops = AsyncDatabaseOps(session)  # Create custom instance for transaction control

    def build_chat_response(self, chat: db_models.Chat) -> view_models.Chat:
        """Build Chat response object for API return."""
        return Chat(
            id=chat.id,
            title=chat.title,
            bot_id=chat.bot_id,
            peer_type=chat.peer_type,
            peer_id=chat.peer_id,
            created=chat.gmt_created.isoformat(),
            updated=chat.gmt_updated.isoformat(),
        )

    async def create_chat(self, user: str, bot_id: str) -> view_models.Chat:
        # First check if bot exists
        bot = await self.db_ops.query_bot(user, bot_id)
        if bot is None:
            raise ResourceNotFoundException("Bot", bot_id)

        # Direct call to repository method, which handles its own transaction
        chat = await self.db_ops.create_chat(user=user, bot_id=bot_id)

        return self.build_chat_response(chat)

    async def list_chats(
        self,
        user: str,
        bot_id: str,
        page: int = 1,
        page_size: int = 50,
    ):
        """List chats with pagination, sorting and search capabilities."""

        # Define sort field mapping
        sort_mapping = {
            "created": db_models.Chat.gmt_created,
        }

        # Define search fields mapping
        search_fields = {"title": db_models.Chat.title}

        async def _execute_paginated_query(session):
            from sqlalchemy import and_, desc, select

            # Build base query
            query = select(db_models.Chat).where(
                and_(
                    db_models.Chat.user == user,
                    db_models.Chat.bot_id == bot_id,
                    db_models.Chat.status != db_models.ChatStatus.DELETED,
                )
            )

            # Build query parameters
            from aperag.utils.pagination import ListParams, PaginationHelper, PaginationParams, SortParams

            params = ListParams(
                pagination=PaginationParams(page=page, page_size=page_size),
                sort=SortParams(sort_by="created", sort_order="desc"),
            )

            # Use pagination helper
            items, total = await PaginationHelper.paginate_query(
                query=query,
                session=session,
                params=params,
                sort_mapping=sort_mapping,
                search_fields=search_fields,
                default_sort=desc(db_models.Chat.gmt_created),
            )

            # Build chat responses
            chat_responses = []
            for chat in items:
                chat_responses.append(self.build_chat_response(chat))

            return PaginationHelper.build_response(items=chat_responses, total=total, page=page, page_size=page_size)

        return await self.db_ops._execute_query(_execute_paginated_query)

    async def get_chat(self, user: str, bot_id: str, chat_id: str) -> view_models.ChatDetails:
        # Import here to avoid circular imports
        from aperag.utils.history import query_chat_messages

        chat = await self.db_ops.query_chat(user, bot_id, chat_id)
        if chat is None:
            raise ChatNotFoundException(chat_id)

        # Get chat history
        messages = await query_chat_messages(user, chat_id)

        # Build response object
        chat_obj = self.build_chat_response(chat)
        return ChatDetails(**chat_obj.model_dump(), history=messages)

    async def update_chat(
        self, user: str, bot_id: str, chat_id: str, chat_in: view_models.ChatUpdate
    ) -> view_models.Chat:
        # First check if chat exists
        chat = await self.db_ops.query_chat(user, bot_id, chat_id)
        if chat is None:
            raise ChatNotFoundException(chat_id)

        # Direct call to repository method, which handles its own transaction
        updated_chat = await self.db_ops.update_chat_by_id(user, bot_id, chat_id, chat_in.title)

        if not updated_chat:
            raise ChatNotFoundException(chat_id)

        return self.build_chat_response(updated_chat)

    async def delete_chat(self, user: str, bot_id: str, chat_id: str) -> Optional[view_models.Chat]:
        """Delete chat by ID (idempotent operation)

        Returns the deleted chat or None if already deleted/not found
        """
        # Check if chat exists - if not, silently succeed (idempotent)
        chat = await self.db_ops.query_chat(user, bot_id, chat_id)
        if chat is None:
            return None

        # Direct call to repository method, which handles its own transaction
        deleted_chat = await self.db_ops.delete_chat_by_id(user, bot_id, chat_id)

        if deleted_chat:
            # Clear chat history from Redis
            history = RedisChatMessageHistory(chat_id, redis_client=get_async_redis_client())
            await history.clear()

            return self.build_chat_response(deleted_chat)

        return None

    def stream_frontend_sse_response(
        self, generator: AsyncGenerator[Any, Any], formatter: FrontendFormatter, msg_id: str
    ):
        """Yield SSE events for FastAPI StreamingResponse."""

        async def event_stream():
            yield f"data: {json.dumps(formatter.format_stream_start(msg_id))}\n\n"
            async for chunk in generator:
                yield f"data: {json.dumps(formatter.format_stream_content(msg_id, chunk))}\n\n"
            yield f"data: {json.dumps(formatter.format_stream_end(msg_id))}\n\n"

        return event_stream()

    async def frontend_chat_completions(
        self,
        user: str,
        message: str,
        stream: bool,
        bot_id: str,
        chat_id: str,
        msg_id: str,
        upload_files: List[str] = None,
    ) -> Any:
        """Frontend chat completions with special error handling for UI responses"""

        # Get document metadata and associate documents with message if files are provided
        from aperag.service.chat_document_service import chat_document_service

        files = await chat_document_service.associate_documents_with_message(
            chat_id=chat_id, message_id=msg_id, files=upload_files or [], user=user
        )

        # Validate bot_id - return formatted error for frontend
        if not bot_id:
            return FrontendFormatter.format_error("bot_id is required")

        bot = await self.db_ops.query_bot(user, bot_id)  # 查询用户可访问的对话机器人信息
        if not bot:
            return FrontendFormatter.format_error("Bot not found")

        # Get or create chat session
        chat = await self.db_ops.query_chat_by_peer(bot.user, db_models.ChatPeerType.FEISHU, chat_id)  # 查询用户对话窗口

        if chat is None:
            # Create chat with peer info atomically in single transaction
            chat = await self.db_ops.create_chat(
                user=bot.user,
                bot_id=bot.id,
                title="Feishu Chat",
                peer_type=db_models.ChatPeerType.FEISHU,
                peer_id=chat_id,
            )

        # Use flow engine instead of MessageProcessor/pipeline
        formatter = FrontendFormatter()

        # Get bot's flow configuration
        bot_config = json.loads(bot.config or "{}")
        flow_config = bot_config.get("flow")
        if not flow_config:
            return FrontendFormatter.format_error("Bot flow config not found")

        try:
            flow = FlowParser.parse(flow_config)
            engine = FlowEngine()

            # Prepare initial data for flow execution
            initial_data = {
                "query": message,
                "user": user,
                "message_id": msg_id or str(uuid.uuid4()),
                "chat_id": chat_id,
            }

            # Save user message to history with file metadata
            from aperag.utils.history import RedisChatMessageHistory, get_async_redis_client

            history = RedisChatMessageHistory(chat_id, redis_client=get_async_redis_client())
            await history.add_user_message(message, msg_id, files=files)

            # Execute flow
            _, system_outputs = await engine.execute_flow(flow, initial_data)
            logger.info("Flow executed successfully!")

            # Find the async generator from flow outputs
            async_generator = None
            nodes = engine.find_end_nodes(flow)
            for node in nodes:
                async_generator = system_outputs[node].get("async_generator")
                if async_generator:
                    break

            if not async_generator:
                return FrontendFormatter.format_error("No output node found")

            # Return streaming or non-streaming response
            if stream:
                return StreamingResponse(
                    self.stream_frontend_sse_response(
                        async_generator(),
                        formatter,
                        msg_id or str(uuid.uuid4()),
                    ),
                    media_type="text/event-stream",
                )
            else:
                # Collect all content for non-streaming response
                full_content = ""
                async for chunk in async_generator():
                    full_content += chunk
                return formatter.format_complete_response(msg_id or str(uuid.uuid4()), full_content)

        except Exception as e:
            logger.exception(e)
            return FrontendFormatter.format_error(str(e))

    async def feedback_message(
        self,
        user: str,
        chat_id: str,
        message_id: str,
        feedback_type: str = None,
        feedback_tag: str = None,
        feedback_message: str = None,
    ) -> dict:
        """Handle message feedback for chat messages"""
        # Get message from Redis history to validate it exists and get context
        history = RedisChatMessageHistory(chat_id, redis_client=get_async_redis_client())
        ai_msg = None
        human_msg = None
        for message in await history.messages:
            if message.message_id != message_id:
                continue
            if message.role == "ai":
                ai_msg = message
            if message.role == "human":
                human_msg = message

        if not ai_msg:
            raise ResourceNotFoundException("AI Message", message_id)
        if not human_msg:
            raise ResourceNotFoundException("Human Message", message_id)

        # Handle feedback state change based on UX design principles
        if feedback_type is None:
            # User wants to remove feedback (cancel like/dislike)
            success_removed = await self.db_ops.remove_message_feedback(user, chat_id, message_id)
            result = {"action": "deleted", "success": success_removed}
        else:
            # User wants to set feedback state (like/dislike)
            feedback = await self.db_ops.set_message_feedback_state(
                user=user,
                chat_id=chat_id,
                message_id=message_id,
                feedback_type=feedback_type,
                feedback_tag=feedback_tag,
                feedback_message=feedback_message,
                question=human_msg.get_main_content(),
                original_answer=ai_msg.get_main_content(),
            )
            result = {"action": "upserted", "feedback": feedback}
        return result

    async def handle_websocket_chat(self, websocket: WebSocket, user: str, bot_id: str, chat_id: str):
        """Handle WebSocket chat connections and message streaming"""
        # -- 连接初始化：接受前端 WebSocket 连接
        """
        关于websocket.accept()的补充说明：
            - 若不调用此方法，前端会一直处于 “连接等待” 状态，最终超时失败；
            - 调用后，前后端进入 “双向通信就绪” 状态，可开始收发消息。
        """
        await websocket.accept()  #  在前端发起连接请求、后端完成身份认证后，通过 websocket.accept() 正式建立前后端的持久连接。
        # -- 前置校验：获取机器人配置并路由业务类型
        # 校验机器人合法性，并基于机器人业务类型，实现 “不同类型机器人走不同处理流程” 的路由逻辑
        try:
            # Get bot configuration first to determine bot type
            bot = await self.db_ops.query_bot(user, bot_id)
            if not bot:
                await websocket.send_text(fail_response("error", "Bot not found"))
                return

            # Route to appropriate service based on bot type
            if bot.type == db_models.BotType.AGENT:  # 若为“智能体类型机器人”，调用专门的 Agent 对话服务【注意默认机器人类型为agent】
                # Use AgentChatService for agent-type bots
                from aperag.service.agent_chat_service import AgentChatService

                agent_service = AgentChatService()  # 初始化agent对话服务
                await agent_service.handle_websocket_agent_chat(websocket, user, bot_id, chat_id)  # agent对话逻辑
                return
            # 若为“知识库机器人”或“普通机器人”，走后续通用流程
            # Continue with existing flow for knowledge and common bots
            # 初始化对话历史管理器，用 Redis 存储当前对话（chat_id 对应的）的历史消息 ——Redis 适合高频读写场景，能快速获取对话上下文。
            history = RedisChatMessageHistory(chat_id, redis_client=get_async_redis_client())
            # -- 核心循环：持续接收前端消息并处理
            while True:  # 通过 while True 实现 “无限循环”，持续监听前端发送的用户提问（直到连接断开），这是 WebSocket “持久连接” 特性的体现
                # Receive message from client
                # 异步等待前端消息（不阻塞其他连接），前端每次发送提问都会触发此方法
                text_data = await websocket.receive_text()  # 接收前端发送的文本消息（前端通过 sendMessage 发送 JSON 字符串）
                data = json.loads(text_data)  # 解析为Python字典（前端传递的参数如 {query: "什么是 RAG？", files: []}）

                # Extract message content - support both "data" and "message" fields
                message_content = data.get("data") or data.get("message", "")  # 提取用户提问内容：兼容“data”或“message”字段（避免前端传参格式不一致）
                if not message_content:
                    # 若提问内容为空，发送错误提示，跳过本次循环
                    await websocket.send_text(fail_response("error", "Message content is required"))
                    continue
                # 生成消息唯一 ID（用 UUID 确保不重复，用于关联后续的回答和参考资料）
                # Generate message ID
                message_id = str(uuid.uuid4())

                # Get document metadata and associate documents with message if files are provided
                from aperag.service.chat_document_service import chat_document_service
                # 若前端上传了文件（如用户上传 Markdown 文档让机器人分析），关联文件与当前消息
                files = await chat_document_service.associate_documents_with_message(
                    chat_id=chat_id, message_id=message_id, files=data.get("files", []), user=user
                )  # 用户可上传文档，后端将文件与当前消息绑定，后续检索时会优先从这些文件中提取信息；
                # 将用户提问（含文件元数据）添加到对话历史（Redis）
                # Add user message to history with file metadata
                await history.add_user_message(message_content, message_id, files=files)  # 对话历史存储：将用户提问存入 Redis，后续调用 LLM 或检索知识库时，可快速获取上下文（如多轮对话中 “上文提到的文档”）

                try:
                    # 校验当前对话窗口（chat_id）是否存在，不存在则创建
                    # Get or create chat session
                    try:
                        await self.db_ops.query_chat(user, bot_id, chat_id)
                    except Exception:
                        # If chat doesn't exist, create it with direct repository call
                        await self.db_ops.create_chat(user=user, bot_id=bot_id, title="WebSocket Chat")
                    # 解析机器人的流程配置（bot.config 是 JSON 字符串，存储 RAG/LLM 调用逻辑）
                    # Get bot's flow configuration
                    bot_config = json.loads(bot.config or "{}")
                    flow_config = bot_config.get("flow")  # 核心配置项，存储机器人的 “处理链路”（如 “用户提问→检索知识库→调用 LLM 生成回答”），后续通过 FlowParser 解析为可执行流程。
                    if not flow_config:
                        # 若流程配置为空（如机器人未配置 RAG 链路），发送错误提示
                        await websocket.send_text(fail_response(message_id, "Bot flow config not found"))
                        continue
                    # -- 流程执行：解析并运行 RAG/LLM 处理链路
                    flow = FlowParser.parse(flow_config)  # 解析流程配置（将 JSON 格式的 flow_config 转化为引擎可执行的流程对象）
                    engine = FlowEngine()  # 初始化流程执行引擎（负责调度流程中的各个节点，如检索节点、LLM 节点）

                    # 准备流程执行的初始参数（传递用户提问、对话历史、消息 ID 等关键信息）
                    # Prepare initial data for flow execution
                    initial_data = {
                        "query": message_content,
                        "user": user,
                        "message_id": message_id,
                        "history": history,
                        "chat_id": chat_id,
                    }

                    # Send start message
                    await websocket.send_text(start_response(message_id))  # 发送“开始处理”消息给前端，前端显示“正在思考”状态

                    # Execute flow
                    _, system_outputs = await engine.execute_flow(flow, initial_data)  # 执行流程（engine.execute_flow 是核心方法，异步运行整个 RAG/LLM 链路）
                    logger.info("Flow executed successfully for WebSocket!")
                    # -- 流式输出：实时推送 AI 回答与参考资料
                    # 从流程输出中找到“异步生成器”（LLM 节点返回的流式输出对象）
                    # Find the async generator from flow outputs
                    async_generator = None  # 生成器作用：避免等待 LLM 生成完整回答后再返回，而是 “生成一段推一段”，降低前端等待时间。
                    nodes = engine.find_end_nodes(flow)
                    for node in nodes:
                        # 从结束节点的输出中提取 async_generator（异步生成器）
                        async_generator = system_outputs[node].get("async_generator")
                        if async_generator:
                            break
                    # 若没有找到生成器，发送错误提示
                    if not async_generator:
                        await websocket.send_text(fail_response(message_id, "No output node found"))
                        continue

                    # Stream response tokens
                    full_message = ""  # 存储完整回答（用于后续可能的日志或存储）
                    references = []  # 存储 RAG 检索到的参考资料（如知识库文档片段）
                    urls = []  # 存储参考资料的链接（如文档下载地址）
                    # 异步遍历生成器，逐段获取 LLM 输出
                    """
                    特殊片段处理：RAG 系统需要返回 “参考资料”，代码通过自定义前缀（如 DOC_QA_REFERENCES:）标记参考资料片段，避免与普通回答混淆；
                    流式推送：async for chunk 逐段获取 LLM 输出，每获取一段就通过 success_response 推送给前端，前端实时更新 UI，提升用户体验。
                    """
                    async for chunk in async_generator():
                        # 处理特殊片段：参考资料标识（DOC_QA_REFERENCES 是自定义前缀）
                        # Handle special tokens for references and URLs (similar to original implementation)
                        if chunk.startswith(DOC_QA_REFERENCES):
                            try:
                                # 提取前缀后的 JSON 内容，解析为参考资料列表
                                references = json.loads(chunk[len(DOC_QA_REFERENCES) :])
                                continue  # 不推送参考资料片段给前端（单独在结束时推送）
                            except Exception as e:
                                logger.exception(f"Error parsing doc qa references: {chunk}, {e}")
                        # 处理特殊片段：文档链接标识（DOCUMENT_URLS 是自定义前缀）
                        if chunk.startswith(DOCUMENT_URLS):
                            try:
                                # 提取前缀后的内容，解析为文档链接列表（用 eval 是为了兼容旧格式，不推荐但常见）
                                urls = eval(chunk[len(DOCUMENT_URLS) :])  # Using eval as in original code
                                continue
                            except Exception as e:
                                logger.exception(f"Error parsing document urls: {chunk}, {e}")
                        # 推送普通回答片段给前端（前端收到后追加到回答区域，实现“打字机效果”）
                        # Send streaming response
                        await websocket.send_text(success_response(message_id, chunk))
                        full_message += chunk
                    """     
                        references_response：推送参考资料（如 {"status":"references","message_id":"xxx","data":[{...}]}），前端收到后显示 “参考文档” 区域；
                        stop_response：推送结束通知，前端关闭加载状态，标记本次回答完成。
                    """
                    # 发送参考资料（含内存占用统计，这里暂为 0，可扩展为实际统计）
                    # Send stop message with references and URLs
                    memory_count = 0  # You might want to implement memory counting if needed
                    await websocket.send_text(references_response(message_id, references, memory_count, urls))
                    # 发送“处理完成”通知，前端隐藏“正在思考”状态
                    await websocket.send_text(stop_response(message_id))
        # -- 异常捕获：处理连接断开与业务错误
                except Exception as e:
                    logger.exception(f"Error processing WebSocket message: {e}")
                    await websocket.send_text(fail_response(message_id, str(e)))

        except WebSocketDisconnect:  # 当前端主动断开连接（如关闭页面、刷新）或网络中断时，触发 WebSocketDisconnect 异常，记录日志后优雅退出循环。
            logger.info(f"WebSocket disconnected for bot {bot_id}, chat {chat_id}")
        except Exception as e:  # 通用异常处理
            logger.exception(f"WebSocket error: {e}")
            try:
                # 发送错误消息给前端，告知用户处理失败
                await websocket.send_text(fail_response("error", str(e)))
            except Exception as e:
                logger.exception(f"Error sending fail response: {e}")


# Create a global service instance for easy access
# This uses the global db_ops instance and doesn't require session management in views
# 全局实例 chat_service_global 供路由层（如之前的 websocket_chat_endpoint）直接调用，无需重复创建 ChatService 对象，减少资源消耗，同时统一管理数据库连接、Redis 客户端等资源。
chat_service_global = ChatService()  # 全局服务实例：方便外部调用
