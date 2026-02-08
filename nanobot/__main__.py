"""CLI 入口模块。

执行 `python -m nanobot` 时会从这里进入 Typer 命令行应用。
"""

from nanobot.cli.commands import app

if __name__ == "__main__":
    app()
