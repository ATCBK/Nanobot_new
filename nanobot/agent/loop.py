"""Agent 循环：核心处理引擎。"""

import asyncio
import json
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider
from nanobot.agent.context import ContextBuilder
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirTool
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.web import WebSearchTool, WebFetchTool
from nanobot.agent.tools.message import MessageTool
from nanobot.agent.tools.spawn import SpawnTool
from nanobot.agent.tools.cron import CronTool
from nanobot.agent.subagent import SubagentManager
from nanobot.session.manager import SessionManager


class AgentLoop:
    """消息处理主引擎。

    职责分工：
    1. 消费入站消息（inbound）。
    2. 组装上下文并调用 LLM。
    3. 执行工具调用并将结果回填到上下文。
    4. 生成并发布出站消息（outbound）。
    5. 持久化会话历史。
    """

    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int = 20,
        brave_api_key: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
        cron_service: "CronService | None" = None,
        restrict_to_workspace: bool = False,
    ):
        from nanobot.config.schema import ExecToolConfig
        from nanobot.cron.service import CronService

        self.bus = bus
        self.provider = provider
        self.workspace = workspace
        self.model = model or provider.get_default_model()
        self.max_iterations = max_iterations
        self.brave_api_key = brave_api_key
        self.exec_config = exec_config or ExecToolConfig()
        self.cron_service = cron_service
        self.restrict_to_workspace = restrict_to_workspace

        self.context = ContextBuilder(workspace)
        self.sessions = SessionManager(workspace)
        self.tools = ToolRegistry()
        self.subagents = SubagentManager(
            provider=provider,
            workspace=workspace,
            bus=bus,
            model=self.model,
            brave_api_key=brave_api_key,
            exec_config=self.exec_config,
            restrict_to_workspace=restrict_to_workspace,
        )

        self._running = False
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """注册默认工具集。"""
        # 文件工具（按配置决定是否限制在工作区）
        allowed_dir = self.workspace if self.restrict_to_workspace else None
        self.tools.register(ReadFileTool(allowed_dir=allowed_dir))
        self.tools.register(WriteFileTool(allowed_dir=allowed_dir))
        self.tools.register(EditFileTool(allowed_dir=allowed_dir))
        self.tools.register(ListDirTool(allowed_dir=allowed_dir))

        # 命令行工具
        self.tools.register(ExecTool(
            working_dir=str(self.workspace),
            timeout=self.exec_config.timeout,
            restrict_to_workspace=self.restrict_to_workspace,
        ))

        # 网络工具
        self.tools.register(WebSearchTool(api_key=self.brave_api_key))
        self.tools.register(WebFetchTool())

        # 消息工具
        message_tool = MessageTool(send_callback=self.bus.publish_outbound)
        self.tools.register(message_tool)

        # 子代理启动工具（用于拉起子代理）
        spawn_tool = SpawnTool(manager=self.subagents)
        self.tools.register(spawn_tool)

        # 定时任务工具（用于定时调度）
        if self.cron_service:
            self.tools.register(CronTool(self.cron_service))

    async def run(self) -> None:
        """运行 Agent 循环，从消息总线持续处理消息。"""
        self._running = True
        logger.info("Agent loop started")

        while self._running:
            try:
                # 等待下一条消息
                msg = await asyncio.wait_for(
                    self.bus.consume_inbound(),
                    timeout=1.0
                )

                # 处理消息
                try:
                    response = await self._process_message(msg)
                    if response:
                        await self.bus.publish_outbound(response)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # 发送错误响应
                    await self.bus.publish_outbound(OutboundMessage(
                        channel=msg.channel,
                        chat_id=msg.chat_id,
                        content=f"Sorry, I encountered an error: {str(e)}"
                    ))
            except asyncio.TimeoutError:
                continue

    def stop(self) -> None:
        """停止 Agent 循环。"""
        self._running = False
        logger.info("Agent loop stopping")

    async def _process_message(self, msg: InboundMessage) -> OutboundMessage | None:
        """
        处理单条入站消息。

        参数：
            msg: 待处理的入站消息。

        返回：
            响应消息；如果不需要响应则返回 None。
        """
        # 处理系统消息（如子代理公告）
        # 会话标识中携带原始“通道:会话编号”，用于路由回原会话
        if msg.channel == "system":
            return await self._process_system_message(msg)

        logger.info(f"Processing message from {msg.channel}:{msg.sender_id}")

        # 获取或创建会话
        session = self.sessions.get_or_create(msg.session_key)

        # 更新工具上下文
        message_tool = self.tools.get("message")
        if isinstance(message_tool, MessageTool):
            message_tool.set_context(msg.channel, msg.chat_id)

        spawn_tool = self.tools.get("spawn")
        if isinstance(spawn_tool, SpawnTool):
            spawn_tool.set_context(msg.channel, msg.chat_id)

        cron_tool = self.tools.get("cron")
        if isinstance(cron_tool, CronTool):
            cron_tool.set_context(msg.channel, msg.chat_id)

        # 构建初始消息（使用历史记录生成模型可用的历史格式）
        messages = self.context.build_messages(
            history=session.get_history(),
            current_message=msg.content,
            media=msg.media if msg.media else None,
            channel=msg.channel,
            chat_id=msg.chat_id,
        )

        # 智能体迭代循环
        iteration = 0
        final_content = None

        while iteration < self.max_iterations:
            iteration += 1

            # 调用大模型
            response = await self.provider.chat(
                messages=messages,
                tools=self.tools.get_definitions(),
                model=self.model
            )

            # 处理工具调用
            if response.has_tool_calls:
                # 将包含工具调用的助手消息写入上下文
                tool_call_dicts = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments)  # 必须是结构化参数字符串
                        }
                    }
                    for tc in response.tool_calls
                ]
                messages = self.context.add_assistant_message(
                    messages, response.content, tool_call_dicts
                )

                # 执行工具
                for tool_call in response.tool_calls:
                    args_str = json.dumps(tool_call.arguments)
                    logger.debug(f"Executing tool: {tool_call.name} with arguments: {args_str}")
                    result = await self.tools.execute(tool_call.name, tool_call.arguments)
                    messages = self.context.add_tool_result(
                        messages, tool_call.id, tool_call.name, result
                    )
            else:
                # 没有工具调用，结束循环
                final_content = response.content
                break

        if final_content is None:
            final_content = "I've completed processing but have no response to give."

        # 保存到会话
        session.add_message("user", msg.content)
        session.add_message("assistant", final_content)
        self.sessions.save(session)

        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=final_content
        )

    async def _process_system_message(self, msg: InboundMessage) -> OutboundMessage | None:
        """
        处理 system 消息（例如子代理公告）。

        chat_id 字段包含 "original_channel:original_chat_id"，用于把响应
        路由回正确目的地。
        """
        logger.info(f"Processing system message from {msg.sender_id}")

        # 从会话标识解析来源（格式：“通道:会话编号”）
        if ":" in msg.chat_id:
            parts = msg.chat_id.split(":", 1)
            origin_channel = parts[0]
            origin_chat_id = parts[1]
        else:
            # 回退默认来源
            origin_channel = "cli"
            origin_chat_id = msg.chat_id

        # 使用来源会话作为上下文
        session_key = f"{origin_channel}:{origin_chat_id}"
        session = self.sessions.get_or_create(session_key)

        # 更新工具上下文
        message_tool = self.tools.get("message")
        if isinstance(message_tool, MessageTool):
            message_tool.set_context(origin_channel, origin_chat_id)

        spawn_tool = self.tools.get("spawn")
        if isinstance(spawn_tool, SpawnTool):
            spawn_tool.set_context(origin_channel, origin_chat_id)

        cron_tool = self.tools.get("cron")
        if isinstance(cron_tool, CronTool):
            cron_tool.set_context(origin_channel, origin_chat_id)

        # 使用公告内容构建消息
        messages = self.context.build_messages(
            history=session.get_history(),
            current_message=msg.content,
            channel=origin_channel,
            chat_id=origin_chat_id,
        )

        # 智能体迭代循环（公告场景下使用）
        iteration = 0
        final_content = None

        while iteration < self.max_iterations:
            iteration += 1

            response = await self.provider.chat(
                messages=messages,
                tools=self.tools.get_definitions(),
                model=self.model
            )

            if response.has_tool_calls:
                tool_call_dicts = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments)
                        }
                    }
                    for tc in response.tool_calls
                ]
                messages = self.context.add_assistant_message(
                    messages, response.content, tool_call_dicts
                )

                for tool_call in response.tool_calls:
                    args_str = json.dumps(tool_call.arguments)
                    logger.debug(f"Executing tool: {tool_call.name} with arguments: {args_str}")
                    result = await self.tools.execute(tool_call.name, tool_call.arguments)
                    messages = self.context.add_tool_result(
                        messages, tool_call.id, tool_call.name, result
                    )
            else:
                final_content = response.content
                break

        if final_content is None:
            final_content = "Background task completed."

        # 保存到会话（在历史中标记为系统消息）
        session.add_message("user", f"[System: {msg.sender_id}] {msg.content}")
        session.add_message("assistant", final_content)
        self.sessions.save(session)

        return OutboundMessage(
            channel=origin_channel,
            chat_id=origin_chat_id,
            content=final_content
        )

    async def process_direct(
        self,
        content: str,
        session_key: str = "cli:direct",
        channel: str = "cli",
        chat_id: str = "direct",
    ) -> str:
        """
        直接处理一条消息（用于 CLI 或 cron 场景）。

        参数：
            content: 消息内容。
            session_key: 会话标识。
            channel: 来源渠道（用于上下文）。
            chat_id: 来源会话 ID（用于上下文）。

        返回：
            Agent 的响应文本。
        """
        msg = InboundMessage(
            channel=channel,
            sender_id="user",
            chat_id=chat_id,
            content=content
        )

        response = await self._process_message(msg)
        return response.content if response else ""
