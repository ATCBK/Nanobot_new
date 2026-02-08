"""模块说明：service。"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Coroutine

from loguru import logger

# 中文注释
DEFAULT_HEARTBEAT_INTERVAL_S = 30 * 60

# 中文注释
HEARTBEAT_PROMPT = """Read HEARTBEAT.md in your workspace (if it exists).
Follow any instructions or tasks listed there.
If nothing needs attention, reply with just: HEARTBEAT_OK"""

# 中文注释
HEARTBEAT_OK_TOKEN = "HEARTBEAT_OK"


def _is_heartbeat_empty(content: str | None) -> bool:
    """函数说明：_is_heartbeat_empty。"""
    if not content:
        return True
    
    # 中文注释
    skip_patterns = {"- [ ]", "* [ ]", "- [x]", "* [x]"}
    
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("<!--") or line in skip_patterns:
            continue
        return False  # 发现可处理内容
    
    return True


class HeartbeatService:
    """类说明：HeartbeatService。"""
    
    def __init__(
        self,
        workspace: Path,
        on_heartbeat: Callable[[str], Coroutine[Any, Any, str]] | None = None,
        interval_s: int = DEFAULT_HEARTBEAT_INTERVAL_S,
        enabled: bool = True,
    ):
        self.workspace = workspace
        self.on_heartbeat = on_heartbeat
        self.interval_s = interval_s
        self.enabled = enabled
        self._running = False
        self._task: asyncio.Task | None = None
    
    @property
    def heartbeat_file(self) -> Path:
        return self.workspace / "HEARTBEAT.md"
    
    def _read_heartbeat_file(self) -> str | None:
        """函数说明：_read_heartbeat_file。"""
        if self.heartbeat_file.exists():
            try:
                return self.heartbeat_file.read_text()
            except Exception:
                return None
        return None
    
    async def start(self) -> None:
        """异步函数说明：start。"""
        if not self.enabled:
            logger.info("Heartbeat disabled")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Heartbeat started (every {self.interval_s}s)")
    
    def stop(self) -> None:
        """函数说明：stop。"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
    
    async def _run_loop(self) -> None:
        """异步函数说明：_run_loop。"""
        while self._running:
            try:
                await asyncio.sleep(self.interval_s)
                if self._running:
                    await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    async def _tick(self) -> None:
        """异步函数说明：_tick。"""
        content = self._read_heartbeat_file()
        
        # 中文注释
        if _is_heartbeat_empty(content):
            logger.debug("Heartbeat: no tasks (HEARTBEAT.md empty)")
            return
        
        logger.info("Heartbeat: checking for tasks...")
        
        if self.on_heartbeat:
            try:
                response = await self.on_heartbeat(HEARTBEAT_PROMPT)
                
                # 中文注释
                if HEARTBEAT_OK_TOKEN.replace("_", "") in response.upper().replace("_", ""):
                    logger.info("Heartbeat: OK (no action needed)")
                else:
                    logger.info(f"Heartbeat: completed task")
                    
            except Exception as e:
                logger.error(f"Heartbeat execution failed: {e}")
    
    async def trigger_now(self) -> str | None:
        """异步函数说明：trigger_now。"""
        if self.on_heartbeat:
            return await self.on_heartbeat(HEARTBEAT_PROMPT)
        return None
