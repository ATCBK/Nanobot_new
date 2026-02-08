"""模块说明：queue。"""

import asyncio
from typing import Callable, Awaitable

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """类说明：MessageBus。"""
    
    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        self._outbound_subscribers: dict[str, list[Callable[[OutboundMessage], Awaitable[None]]]] = {}
        self._running = False
    
    async def publish_inbound(self, msg: InboundMessage) -> None:
        """异步函数说明：publish_inbound。"""
        await self.inbound.put(msg)
    
    async def consume_inbound(self) -> InboundMessage:
        """异步函数说明：consume_inbound。"""
        return await self.inbound.get()
    
    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """异步函数说明：publish_outbound。"""
        await self.outbound.put(msg)
    
    async def consume_outbound(self) -> OutboundMessage:
        """异步函数说明：consume_outbound。"""
        return await self.outbound.get()
    
    def subscribe_outbound(
        self, 
        channel: str, 
        callback: Callable[[OutboundMessage], Awaitable[None]]
    ) -> None:
        """函数说明：subscribe_outbound。"""
        if channel not in self._outbound_subscribers:
            self._outbound_subscribers[channel] = []
        self._outbound_subscribers[channel].append(callback)
    
    async def dispatch_outbound(self) -> None:
        """异步函数说明：dispatch_outbound。"""
        self._running = True
        while self._running:
            try:
                msg = await asyncio.wait_for(self.outbound.get(), timeout=1.0)
                subscribers = self._outbound_subscribers.get(msg.channel, [])
                for callback in subscribers:
                    try:
                        await callback(msg)
                    except Exception as e:
                        logger.error(f"Error dispatching to {msg.channel}: {e}")
            except asyncio.TimeoutError:
                continue
    
    def stop(self) -> None:
        """函数说明：stop。"""
        self._running = False
    
    @property
    def inbound_size(self) -> int:
        """函数说明：inbound_size。"""
        return self.inbound.qsize()
    
    @property
    def outbound_size(self) -> int:
        """函数说明：outbound_size。"""
        return self.outbound.qsize()
