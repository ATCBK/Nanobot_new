"""工具注册与调度模块。

ToolRegistry 把“工具定义管理”和“工具执行入口”集中在一处，
让 AgentLoop 只关心调用，不关心每个工具的具体实现。
"""

from typing import Any

from nanobot.agent.tools.base import Tool


class ToolRegistry:
    """工具容器与执行分发器。"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册工具；同名工具会被后注册者覆盖。"""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """注销工具；不存在时静默忽略。"""
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        """按名称获取工具实例。"""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """判断工具是否已注册。"""
        return name in self._tools

    def get_definitions(self) -> list[dict[str, Any]]:
        """导出 OpenAI function calling 格式的工具定义列表。"""
        return [tool.to_schema() for tool in self._tools.values()]

    async def execute(self, name: str, params: dict[str, Any]) -> str:
        """执行指定工具。

        执行前会先做参数校验，避免把非法参数交给工具实现。
        """
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"

        try:
            errors = tool.validate_params(params)
            if errors:
                return f"Error: Invalid parameters for tool '{name}': " + "; ".join(errors)
            return await tool.execute(**params)
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    @property
    def tool_names(self) -> list[str]:
        """返回已注册工具名列表（用于调试与展示）。"""
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
