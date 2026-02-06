"""Discord channel implementation using discord.py."""

import asyncio
from typing import Any

import discord
from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import DiscordConfig


class DiscordChannel(BaseChannel):
    """
    Discord channel using discord.py.
    """
    
    name = "discord"
    
    def __init__(self, config: DiscordConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: DiscordConfig = config
        
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        self._setup_events()
        
    def _setup_events(self):
        @self.client.event
        async def on_ready():
            logger.info(f"Discord logged in as {self.client.user}")
            
        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
                
            sender_id = str(message.author.id)
            username = str(message.author.name)
            
            # Combine ID and username for easier allow_from matching
            sender_identity = f"{sender_id}|{username}"
            
            content = message.content
            
            # Handle attachments (basic image support)
            media = []
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    media.append(attachment.url)
            
            if media:
                content += "\n" + "\n".join([f"[Image: {url}]" for url in media])
            
            await self._handle_message(
                sender_id=sender_identity,
                chat_id=str(message.channel.id),
                content=content,
                media=media,
                metadata={
                    "message_id": message.id,
                    "author_id": message.author.id,
                    "author_name": message.author.name,
                    "guild_id": message.guild.id if message.guild else None,
                    "channel_name": message.channel.name if hasattr(message.channel, "name") else "DM"
                }
            )

    async def start(self) -> None:
        """Start the Discord client."""
        if not self.config.token:
            logger.error("Discord token not configured")
            return
            
        logger.info("Starting Discord channel...")
        try:
            # discord.py client.start is an async context manager or coroutine?
            # It's a coroutine.
            await self.client.start(self.config.token)
        except Exception as e:
            logger.error(f"Discord connection error: {e}")

    async def stop(self) -> None:
        """Stop the Discord client."""
        if self.client:
            await self.client.close()

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message to Discord."""
        try:
            # channel_id must be int for discord.py
            try:
                channel_id = int(msg.chat_id)
            except ValueError:
                logger.error(f"Invalid Discord channel ID: {msg.chat_id}")
                return

            channel = self.client.get_channel(channel_id)
            if not channel:
                # Try fetching if not in cache
                try:
                    channel = await self.client.fetch_channel(channel_id)
                except Exception:
                    logger.error(f"Discord channel {channel_id} not found")
                    return
            
            await channel.send(msg.content)
            
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
