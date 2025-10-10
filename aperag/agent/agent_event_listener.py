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
import logging
from typing import Dict

from mcp_agent.logging.listeners import EventListener
from mcp_agent.logging.transport import AsyncEventBus, Event

from aperag.agent import AgentMessageQueue
from aperag.agent.agent_event_processor import AgentEventProcessor

logger = logging.getLogger(__name__)


class AgentEventListener(EventListener):
    """
    A thread-safe, singleton proxy listener that is registered once and never removed.
    It solves the "dictionary changed size during iteration" race condition by
    managing its own internal, locked collection of temporary AgentEventProcessors,
    and uses the trace_id from the event to dispatch it to the correct listener.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentEventListener, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self):
        """Initializes the singleton instance and registers itself with the event bus."""
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            self._request_listeners: Dict[str, AgentEventProcessor] = {}
            self._bus = AsyncEventBus.get()
            self._bus.add_listener("global", self)  # Register self, permanently
            self._initialized = True
            logger.info("AgentEventListener initialized and registered permanently.")

    async def register_listener(
        self,
        trace_id: str,  # 链路追踪ID（关联当前对话链路）
        chat_id: str,  # 对话ID（关联当前对话窗口）
        message_id: str,  # 消息ID（关联当前用户提问）
        queue: AgentMessageQueue,  # 消息队列（用于传递工具结果）
        language,  # 语言标识（用于格式化多语言响应）
    ):
        """
        安全地为一个特定的请求创建并注册一个agentteventprocessor，由它的trace_id指定。
        """
        """
        Safely creates and registers a AgentEventProcessor for a specific request,
        keyed by its trace_id.
        """
        """
        为当前用户提问（message_id）创建专属的 AgentEventProcessor 实例，将 “链路追踪（trace_id）、业务上下文（chat_id/message_id）、结果传递载体（queue）” 三者绑定，确保监听器只处理 “当前链路、当前对话、当前提问” 的事件。
        """
        listener = AgentEventProcessor(
            message_queue=queue,  # 绑定消息队列（结果最终写入这里）
            trace_id=trace_id,  # 绑定链路ID（确保只处理当前链路的事件）
            chat_id=chat_id,  # 绑定对话ID（业务上下文关联）
            message_id=message_id,  # 绑定消息ID（确保结果关联当前提问）
            language=language,  # 绑定语言（格式化响应文本）
        )  # 创建事件处理器实例（核心逻辑载体）
        """
        通过 async with self._lock 加异步锁，避免多并发请求（如同时有多个用户提问）在修改 self._request_listeners（监听器字典）时出现 “键冲突” 或 “数据覆盖”—— 例如，两个请求同时用相同 trace_id 注册监听器，加锁后可确保后注册的监听器不会被前一个覆盖（虽 trace_id 全局唯一，但并发场景下仍需防护）。
        """
        async with self._lock:  # 加锁注册监听器，确保线程安全
            """
            将监听器存入 self._request_listeners（以 trace_id 为 key），后续系统中产生的 “工具调用事件” 会根据 trace_id 找到对应的监听器，实现 “事件 - 监听器” 的精准匹配。
            """
            self._request_listeners[trace_id] = listener  # 用trace_id作为key存储监听器
            logger.debug(f"Registered temporary listener for trace_id: {trace_id}")

    async def unregister_listener(self, trace_id: str):
        """Safely unregisters a temporary listener by its trace_id."""
        async with self._lock:
            if trace_id in self._request_listeners:
                del self._request_listeners[trace_id]
                logger.debug(f"Unregistered temporary listener for trace_id: {trace_id}")

    async def handle_event(self, event: Event):
        """
        Handles an event from the main bus and forwards it to the specific
        listener associated with the event's trace_id.
        """
        # Assuming the mcp-agent's OTel instrumentation adds trace_id to the event.
        # This is a critical assumption for this pattern to work.
        trace_id = event.trace_id
        if not trace_id:
            logger.warning("Received event without a trace_id. Cannot dispatch.")
            return

        # async with self._lock:
        #     # Find the specific listener for this trace_id
        #     listener = self._request_listeners.get(str(trace_id))

        listener = self._request_listeners.get(str(trace_id))

        if listener:
            # Dispatch the event only to the correct listener
            await listener.handle_event(event)
        else:
            logger.warning(f"Received event for trace_id {trace_id} but no listener was registered.")


# Create a single instance for the application to use
agent_event_listener = AgentEventListener()
