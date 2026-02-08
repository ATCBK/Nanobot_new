"""模块说明：base。"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus


class BaseChannel(ABC):
    """类说明：BaseChannel。"""
    
    name: str = "base"
    
    def __init__(self, config: Any, bus: MessageBus):
        """函数说明：__init__。"""
        self.config = config
        self.bus = bus
        self._running = False
    
    @abstractmethod
    async def start(self) -> None:
        """异步函数说明：start。"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """异步函数说明：stop。"""
        pass
    
    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """异步函数说明：send。"""
        pass
    
    def is_allowed(self, sender_id: str) -> bool:
        """函数说明：is_allowed。"""
        allow_list = getattr(self.config, "allow_from", [])
        
        # 中文注释
        if not allow_list:
            return True
        
        sender_str = str(sender_id)
        if sender_str in allow_list:
            return True
        if "|" in sender_str:
            for part in sender_str.split("|"):
                if part and part in allow_list:
                    return True
        return False
    
    async def _handle_message(
        self,
        sender_id: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """异步函数说明：_handle_message。"""
        if not self.is_allowed(sender_id):
            logger.warning(
                f"Access denied for sender {sender_id} on channel {self.name}. "
                f"Add them to allowFrom list in config to grant access."
            )
            return
        
        msg = InboundMessage(
            channel=self.name,
            sender_id=str(sender_id),
            chat_id=str(chat_id),
            content=content,
            media=media or [],
            metadata=metadata or {}
        )
        
        await self.bus.publish_inbound(msg)
    
    @property
    def is_running(self) -> bool:
        """函数说明：is_running。"""
        return self._running
