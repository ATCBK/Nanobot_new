"""模块说明：telegram。"""

import asyncio
import re

from loguru import logger
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import TelegramConfig


def _markdown_to_telegram_html(text: str) -> str:
    """函数说明：_markdown_to_telegram_html。"""
    if not text:
        return ""
    
    # 中文注释
    code_blocks: list[str] = []
    def save_code_block(m: re.Match) -> str:
        code_blocks.append(m.group(1))
        return f"\x00CB{len(code_blocks) - 1}\x00"
    
    text = re.sub(r'```[\w]*\n?([\s\S]*?)```', save_code_block, text)
    
    # 中文注释
    inline_codes: list[str] = []
    def save_inline_code(m: re.Match) -> str:
        inline_codes.append(m.group(1))
        return f"\x00IC{len(inline_codes) - 1}\x00"
    
    text = re.sub(r'`([^`]+)`', save_inline_code, text)
    
    # 中文注释
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # 中文注释
    text = re.sub(r'^>\s*(.*)$', r'\1', text, flags=re.MULTILINE)
    
    # 中文注释
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 中文注释
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # 中文注释
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    
    # 中文注释
    text = re.sub(r'(?<![a-zA-Z0-9])_([^_]+)_(?![a-zA-Z0-9])', r'<i>\1</i>', text)
    
    # 中文注释
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    
    # 中文注释
    text = re.sub(r'^[-*]\s+', '• ', text, flags=re.MULTILINE)
    
    # 中文注释
    for i, code in enumerate(inline_codes):
        # 中文注释
        escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace(f"\x00IC{i}\x00", f"<code>{escaped}</code>")
    
    # 中文注释
    for i, code in enumerate(code_blocks):
        # 中文注释
        escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace(f"\x00CB{i}\x00", f"<pre><code>{escaped}</code></pre>")
    
    return text


class TelegramChannel(BaseChannel):
    """类说明：TelegramChannel。"""
    
    name = "telegram"
    
    def __init__(self, config: TelegramConfig, bus: MessageBus, groq_api_key: str = ""):
        super().__init__(config, bus)
        self.config: TelegramConfig = config
        self.groq_api_key = groq_api_key
        self._app: Application | None = None
        self._chat_ids: dict[str, int] = {}  # 将 sender_id 映射到 chat_id 以便回复
    
    async def start(self) -> None:
        """异步函数说明：start。"""
        if not self.config.token:
            logger.error("Telegram bot token not configured")
            return
        
        self._running = True
        
        # 中文注释
        self._app = (
            Application.builder()
            .token(self.config.token)
            .build()
        )
        
        # 中文注释
        self._app.add_handler(
            MessageHandler(
                (filters.TEXT | filters.PHOTO | filters.VOICE | filters.AUDIO | filters.Document.ALL) 
                & ~filters.COMMAND, 
                self._on_message
            )
        )
        
        # 中文注释
        from telegram.ext import CommandHandler
        self._app.add_handler(CommandHandler("start", self._on_start))
        
        logger.info("Starting Telegram bot (polling mode)...")
        
        # 中文注释
        await self._app.initialize()
        await self._app.start()
        
        # 中文注释
        bot_info = await self._app.bot.get_me()
        logger.info(f"Telegram bot @{bot_info.username} connected")
        
        # 中文注释
        await self._app.updater.start_polling(
            allowed_updates=["message"],
            drop_pending_updates=True  # 启动时忽略历史消息
        )
        
        # 中文注释
        while self._running:
            await asyncio.sleep(1)
    
    async def stop(self) -> None:
        """异步函数说明：stop。"""
        self._running = False
        
        if self._app:
            logger.info("Stopping Telegram bot...")
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
            self._app = None
    
    async def send(self, msg: OutboundMessage) -> None:
        """异步函数说明：send。"""
        if not self._app:
            logger.warning("Telegram bot not running")
            return
        
        try:
            # 中文注释
            chat_id = int(msg.chat_id)
            # 中文注释
            html_content = _markdown_to_telegram_html(msg.content)
            await self._app.bot.send_message(
                chat_id=chat_id,
                text=html_content,
                parse_mode="HTML"
            )
        except ValueError:
            logger.error(f"Invalid chat_id: {msg.chat_id}")
        except Exception as e:
            # 中文注释
            logger.warning(f"HTML parse failed, falling back to plain text: {e}")
            try:
                await self._app.bot.send_message(
                    chat_id=int(msg.chat_id),
                    text=msg.content
                )
            except Exception as e2:
                logger.error(f"Error sending Telegram message: {e2}")
    
    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """异步函数说明：_on_start。"""
        if not update.message or not update.effective_user:
            return
        
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Hi {user.first_name}! I'm nanobot.\n\n"
            "Send me a message and I'll respond!"
        )
    
    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """异步函数说明：_on_message。"""
        if not update.message or not update.effective_user:
            return
        
        message = update.message
        user = update.effective_user
        chat_id = message.chat_id
        
        # 中文注释
        sender_id = str(user.id)
        if user.username:
            sender_id = f"{sender_id}|{user.username}"
        
        # 中文注释
        self._chat_ids[sender_id] = chat_id
        
        # 中文注释
        content_parts = []
        media_paths = []
        
        # 中文注释
        if message.text:
            content_parts.append(message.text)
        if message.caption:
            content_parts.append(message.caption)
        
        # 中文注释
        media_file = None
        media_type = None
        
        if message.photo:
            media_file = message.photo[-1]  # 最大尺寸照片
            media_type = "image"
        elif message.voice:
            media_file = message.voice
            media_type = "voice"
        elif message.audio:
            media_file = message.audio
            media_type = "audio"
        elif message.document:
            media_file = message.document
            media_type = "file"
        
        # 中文注释
        if media_file and self._app:
            try:
                file = await self._app.bot.get_file(media_file.file_id)
                ext = self._get_extension(media_type, getattr(media_file, 'mime_type', None))
                
                # 中文注释
                from pathlib import Path
                media_dir = Path.home() / ".nanobot" / "media"
                media_dir.mkdir(parents=True, exist_ok=True)
                
                file_path = media_dir / f"{media_file.file_id[:16]}{ext}"
                await file.download_to_drive(str(file_path))
                
                media_paths.append(str(file_path))
                
                # 中文注释
                if media_type == "voice" or media_type == "audio":
                    from nanobot.providers.transcription import GroqTranscriptionProvider
                    transcriber = GroqTranscriptionProvider(api_key=self.groq_api_key)
                    transcription = await transcriber.transcribe(file_path)
                    if transcription:
                        logger.info(f"Transcribed {media_type}: {transcription[:50]}...")
                        content_parts.append(f"[transcription: {transcription}]")
                    else:
                        content_parts.append(f"[{media_type}: {file_path}]")
                else:
                    content_parts.append(f"[{media_type}: {file_path}]")
                    
                logger.debug(f"Downloaded {media_type} to {file_path}")
            except Exception as e:
                logger.error(f"Failed to download media: {e}")
                content_parts.append(f"[{media_type}: download failed]")
        
        content = "\n".join(content_parts) if content_parts else "[empty message]"
        
        logger.debug(f"Telegram message from {sender_id}: {content[:50]}...")
        
        # 中文注释
        await self._handle_message(
            sender_id=sender_id,
            chat_id=str(chat_id),
            content=content,
            media=media_paths,
            metadata={
                "message_id": message.message_id,
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "is_group": message.chat.type != "private"
            }
        )
    
    def _get_extension(self, media_type: str, mime_type: str | None) -> str:
        """函数说明：_get_extension。"""
        if mime_type:
            ext_map = {
                "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
                "audio/ogg": ".ogg", "audio/mpeg": ".mp3", "audio/mp4": ".m4a",
            }
            if mime_type in ext_map:
                return ext_map[mime_type]
        
        type_map = {"image": ".jpg", "voice": ".ogg", "audio": ".mp3", "file": ""}
        return type_map.get(media_type, "")
