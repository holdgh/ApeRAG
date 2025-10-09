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

"""Message queue for agent chat communication."""

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AgentMessageQueue:
    """
    用于代理聊天通信的异步消息队列。
    就像Go频道一样——生产者发送信息，消费者接收信息。
    支持优雅的关闭和流结束信令。
    """
    """
    Async message queue for agent chat communication.

    Acts like Go channels - producers put messages, consumers get messages.
    Supports graceful shutdown and end-of-stream signaling.
    """

    def __init__(self):
        self.queue = asyncio.Queue()
        self._closed = False

    async def put(self, message: Dict[str, Any]) -> None:  # 将消息放入队列
        """Put a message into the queue"""
        if self._closed:
            logger.warning(f"Attempted to put message into closed queue, message: {message}")
            return

        await self.queue.put(message)
        logger.debug(f"Message queued: {message.get('type', 'unknown')}")

    async def get(self) -> Optional[Dict[str, Any]]:  # 从队列中获取消息。当队列关闭且为空时返回None。
        """Get a message from the queue. Returns None when queue is closed and empty."""
        try:
            return await self.queue.get()
        except asyncio.CancelledError:
            return None

    async def close(self) -> None:
        """Close the queue and signal end of stream"""
        self._closed = True
        # Put a sentinel value to signal end of stream
        await self.queue.put(None)  # 设置一个哨兵值来表示流的结束
        logger.debug("Message queue closed")

    def is_closed(self) -> bool:
        """Check if the queue is closed"""
        return self._closed

    def qsize(self) -> int:
        """Get the current queue size"""
        return self.queue.qsize()
