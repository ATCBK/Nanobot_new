"""模块说明：events。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class InboundMessage:
    """类说明：InboundMessage。"""
    
    channel: str  # 渠道类型：telegram、discord、slack、whatsapp
    sender_id: str  # 用户标识
    chat_id: str  # 会话/频道标识
    content: str  # 消息文本
    timestamp: datetime = field(default_factory=datetime.now)
    media: list[str] = field(default_factory=list)  # 媒体 URL 列表
    metadata: dict[str, Any] = field(default_factory=dict)  # 渠道特定数据
    
    @property
    def session_key(self) -> str:
        """函数说明：session_key。"""
        return f"{self.channel}:{self.chat_id}"


@dataclass
class OutboundMessage:
    """类说明：OutboundMessage。"""
    
    channel: str
    chat_id: str
    content: str
    reply_to: str | None = None
    media: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

