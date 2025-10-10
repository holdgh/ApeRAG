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

"""Universal event listener for MCP agent events."""

import logging
from typing import Any, Dict, Optional

from mcp_agent.logging.events import Event
from mcp_agent.logging.listeners import EventListener

from .agent_message_queue import AgentMessageQueue
from .exceptions import EventListenerError, handle_agent_error
from .stream_formatters import format_tool_call_result
from .tool_use_message_formatters import (
    ToolResultFormatter,
)

logger = logging.getLogger(__name__)


class AgentEventProcessor(EventListener):
    """
    AgentEventProcessor 继承自 EventListener，是 “捕获工具调用事件、处理工具结果、转发到消息队列” 的具体实现
    核心逻辑在 handle_event（事件过滤）和 _handle_tool_response（结果处理）两个方法。
    """
    def __init__(
        self,
        message_queue: AgentMessageQueue,
        trace_id: str,
        chat_id: str,
        message_id: str,
        language: str = "en-US",
        context: Optional[Dict[str, Any]] = None,
    ):
        self.message_queue = message_queue
        self.trace_id = trace_id
        self.chat_id = chat_id
        self.message_id = message_id
        self.language = language
        self.formatter = ToolResultFormatter(language, context)

    @handle_agent_error("event_handling", reraise=False)  # 异常捕获装饰器，避免崩溃
    async def handle_event(self, event: Event):  # 事件过滤与路由
        # -- 过滤无效事件（无事件对象或无事件内容）
        if not event or not event.message:
            return
        # -- 过滤非当前链路的事件（确保只处理自己负责的trace_id事件）
        if self.trace_id != event.trace_id:
            logger.warning(
                f"Event trace_id {event.trace_id} does not match listener trace_id {self.trace_id}, ignoring event."
            )
            return
        # -- 路由到工具响应处理逻辑（只处理“工具调用结果”类型的事件）
        if event.message == "send_request: response=":  # event.message == "send_request: response="是当前系统约定的 “工具调用结果事件” 标识
            await self._handle_tool_response(event)

    @handle_agent_error("tool_response_handling", reraise=False)
    async def _handle_tool_response(self, event: Event):  # 工具结果处理与转发
        # -- 校验工具结果数据格式
        if not event.data or not isinstance(event.data, dict):  # 校验事件数据是否存在且为字典
            raise EventListenerError(
                "tool_response", "Invalid event data structure", event_data={"has_data": bool(event.data)}
            )

        data_field = event.data.get("data")  # 提取工具结果的核心字段（data_field是工具返回的结构化数据）
        if not data_field or not isinstance(data_field, dict):
            raise EventListenerError(
                "tool_response", "Missing or invalid data field", event_data={"data_type": type(data_field).__name__}
            )
        # -- 提取工具结果关键信息
        structured_content = data_field.get("structuredContent")  # 工具返回的结构化内容（如搜索结果、表格数据）
        is_error = data_field.get("isError", False)  # 工具调用是否出错（如API超时、参数错误）
        # -- 过滤错误结果（用户反馈不需要显示错误，直接跳过）
        # Skip error calls as requested by user feedback
        if is_error:
            return
        # -- 解析工具结果类型
        """
        formatter（ToolResultFormatter）：工具结果格式化器，负责识别结果类型并解析
        interface_type：结果类型（如“search”搜索结果、“calculator”计算结果、“table”表格结果）
        typed_result：解析后的结构化数据（如搜索结果列表、计算结果数值）
        """
        interface_type, typed_result = self.formatter.detect_and_parse_result(structured_content)
        if interface_type == "unknown":
            return
        # -- 判断是否需要展示结果
        # Use simplified logic to determine if we should display this result
        if not self.formatter.should_display_result(interface_type, typed_result, structured_content):  # 根据结果类型和内容，判断是否需要推送给前端（如某些内部工具结果无需展示）
            return
        # -- 格式化结果为前端可展示文本
        display_text = self.formatter.format_tool_response(interface_type, typed_result, structured_content, is_error)
        # -- 写入消息队列，等待推送给前端
        formatted_message = format_tool_call_result(self.message_id, display_text + "\n\n", interface_type, None)  # 格式化消息格式（符合前端预期的结构，包含message_id、工具类型、展示文本）
        await self.message_queue.put(formatted_message)  # # 将格式化后的消息写入消息队列（后续由consumer任务推送给前端）

        logger.debug(
            f"Tool response captured for message {self.message_id}: {interface_type} (typed: {typed_result is not None})"
        )
