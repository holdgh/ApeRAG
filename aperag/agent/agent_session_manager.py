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

"""Simple agent session management - optimized for ease of maintenance and minimal bugs."""

import asyncio
import logging
import time
from typing import Dict, Optional

from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

from aperag.agent.agent_config import AgentConfig
from aperag.agent.exceptions import AgentConfigurationError
from aperag.agent.mcp_app_factory import MCPAppFactory

logger = logging.getLogger(__name__)


class ChatSession:
    """
    Chat session per user+chat+provider combination.

    Key insight: Each chat session maintains its own MCPApp, Agent, and LLM instances
    to preserve conversation state and memory. Same provider can serve multiple models,
    but each chat has its own isolated session.
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.last_used = time.time()

        # MCP resources - created once per chat session
        self.mcp_app = None
        self.mcp_app_context_manager = None
        self.mcp_running_app = None
        self.agent = None
        self.llm = None  # Cache LLM instance for this chat

        # Simple state flags
        self._ready = False

    async def initialize(self):
        """Initialize with provider settings from config."""
        if self._ready:
            return

        try:
            logger.info(f"Initializing provider session {self.config.get_session_key()}")
            """
            MCP 是一套 “工具管理与执行框架”，负责将 Agent 所需的能力（如知识库检索、网络搜索、文件解析）封装为标准化的 “可调用模块”，并提供统一的调用接口。
            LLM 本身不具备 “检索数据库”“调用外部 API” 的能力，必须通过 MCP 工具才能将 “决策” 转化为 “实际操作”。
            
            绑定逻辑解读：
                MCP 是 “工具容器”：self.mcp_running_app 是启动后的 MCP 实例，内部已加载所有配置好的工具（如知识库检索工具 knowledge_search、网络搜索工具 web_search），且通过 session_id 与当前对话绑定，避免工具调用结果混淆；
                Agent 是 “翻译官”：Agent 初始化时传入了 instruction（系统提示词），提示词中包含 “如何使用工具” 的规则（如 “用户指定知识库后必须调用检索工具”）；同时 Agent 通过 server_names 知道要调用 MCP 中的哪些工具服务；
                LLM 是 “决策者”：通过 agent.attach_llm 方法，LLM 被 “挂载” 到 Agent 上 —— 此时 LLM 并非直接与 MCP 交互，而是通过 Agent 获得 “调用工具的接口”，Agent 会将 LLM 的 “自然语言决策” 转化为 MCP 能理解的 “工具调用指令”。

            """
            # -- 基于AgentConfig创建MCP应用（工具执行环境）
            # Create MCP app for this provider using config
            self.mcp_app = MCPAppFactory.create_mcp_app_from_config(self.config)
            # -- 启动MCP应用，获取运行中的实例（_aenter__是异步上下文管理器，启动服务）
            # Start MCP app
            self.mcp_app_context_manager = self.mcp_app.run()
            self.mcp_running_app = await self.mcp_app_context_manager.__aenter__()
            # -- 给MCP应用绑定当前会话ID（确保工具调用结果能关联到当前对话）
            self.mcp_running_app.context.session_id = self.config.chat_id
            # -- 创建Agent实例（中间协调者），传入系统提示词（关键：提示词包含工具使用规则）
            # Create reusable agent for this chat session
            self.agent = Agent(
                name=f"aperag_agent_{self.config.user_id}_{self.config.chat_id}_{self.config.provider_name}",
                instruction=self.config.instruction,  # 系统提示词（如“优先检索用户指定知识库”）
                server_names=self.config.server_names,  # 可访问的MCP服务名称列表（指定要调用的工具组）【根据 server_names 中的值，在 “已注册的 MCP 服务列表” 中筛选出可调用的服务】
            )

            await self.agent.__aenter__()  # 启动Agent，建立与MCP的通信
            # -- 将LLM附加到Agent上（核心：LLM通过Agent获得调用MCP工具的能力）
            # Create and cache LLM instance for this chat session
            self.llm = await self.agent.attach_llm(OpenAIAugmentedLLM)
            from mcp_agent.logging.logger import get_logger

            self.llm.logger = get_logger(self.llm.name, session_id=self.llm.context.session_id)
            self._ready = True

            logger.info(f"Chat session {self.config.get_session_key()} ready")

        except Exception as e:
            logger.error(f"Failed to initialize session {self.config.get_session_key()}: {e}")
            await self._cleanup()
            raise AgentConfigurationError(f"Session init failed: {e}")

    async def get_llm(self, model: str) -> OpenAIAugmentedLLM:
        """Get cached LLM instance for this chat session."""
        if not self._ready:
            raise AgentConfigurationError("Session not ready")

        # Return the cached LLM instance
        # This preserves conversation state and memory for the chat session
        return self.llm

    def touch(self):
        """Update last used time."""
        self.last_used = time.time()

    def is_expired(self, timeout: int = 1800) -> bool:  # 30 min default
        """Check if session expired."""
        return time.time() - self.last_used > timeout

    async def _cleanup(self):
        """Clean up all resources."""
        logger.info(f"Cleaning up chat session {self.config.get_session_key()}")

        # LLM cleanup is handled by agent cleanup
        self.llm = None

        if self.agent:
            try:
                await self.agent.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Agent cleanup error: {e}")
            self.agent = None

        if self.mcp_app_context_manager:
            try:
                await self.mcp_app_context_manager.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"MCP app cleanup error: {e}")
            self.mcp_running_app = None

        self.mcp_app = None
        self._ready = False


# Simple global state - no complex singleton patterns
_chat_sessions: Dict[str, ChatSession] = {}  # 聊天会话缓存
_cleanup_task: Optional[asyncio.Task] = None


def generate_session_key(user_id: str, chat_id: str, provider_name: str) -> str:
    """Generate session key based on user, chat, and provider."""
    return f"{user_id}:{chat_id}:{provider_name}"


async def get_or_create_session(config: AgentConfig) -> ChatSession:
    """
    使用AgentConfig获取或创建聊天会话。超级简单-没有复杂的锁定。
    为了简单起见，我们接受一些次要的竞争条件。最糟糕的情况:
    我们创建一个额外的会话，稍后进行清理。
    """
    """
    Get or create chat session using AgentConfig. Super simple - no complex locking.

    We accept some minor race conditions for simplicity. Worst case:
    we create an extra session that gets cleaned up later.
    """
    session_key = config.get_session_key()  # 基于agent配置获取聊天会话key【会话key组成规则：“用户id:对话窗口id:模型提供商名称”】

    # Quick check if session exists and is ready
    session = _chat_sessions.get(session_key)
    if session and session._ready and not session.is_expired():
        session.touch()
        return session

    # Need new session - clean up old one if exists
    if session:
        try:
            await session._cleanup()
        except Exception as e:
            logger.warning(f"Error cleaning up old session: {e}")

    # Create fresh session with config
    session = ChatSession(config)
    await session.initialize()

    # Store in global dict
    _chat_sessions[session_key] = session
    logger.info(f"Created new chat session: {session_key}")

    return session


async def cleanup_expired_sessions():
    """Simple cleanup - remove expired chat sessions."""
    expired_keys = []

    for key, session in _chat_sessions.items():
        if session.is_expired():
            expired_keys.append(key)

    for key in expired_keys:
        session = _chat_sessions.pop(key, None)
        if session:
            try:
                await session._cleanup()
                logger.info(f"Cleaned up expired chat session: {key}")
            except Exception as e:
                logger.error(f"Error cleaning chat session {key}: {e}")


async def _cleanup_loop():
    """Background cleanup task."""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            await cleanup_expired_sessions()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Cleanup loop error: {e}")


async def start_cleanup():
    """Start background cleanup task."""
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = asyncio.create_task(_cleanup_loop())
        logger.info("Started session cleanup task")


async def shutdown_all():
    """Shutdown all chat sessions and cleanup task."""
    global _cleanup_task

    # Stop cleanup task
    if _cleanup_task:
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        _cleanup_task = None

    # Clean up all chat sessions
    sessions = list(_chat_sessions.values())
    _chat_sessions.clear()

    for session in sessions:
        try:
            await session._cleanup()
        except Exception as e:
            logger.error(f"Error during shutdown cleanup: {e}")

    logger.info("All chat sessions cleaned up")


def get_stats() -> Dict:
    """Get simple stats."""
    return {
        "total_sessions": len(_chat_sessions),
        "active_sessions": sum(1 for s in _chat_sessions.values() if s._ready),
        "expired_sessions": sum(1 for s in _chat_sessions.values() if s.is_expired()),
    }
