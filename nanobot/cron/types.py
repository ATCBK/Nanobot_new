"""模块说明：types。"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class CronSchedule:
    """类说明：CronSchedule。"""
    kind: Literal["at", "every", "cron"]
    # 中文注释
    at_ms: int | None = None
    # 中文注释
    every_ms: int | None = None
    # 中文注释
    expr: str | None = None
    # 中文注释
    tz: str | None = None


@dataclass
class CronPayload:
    """类说明：CronPayload。"""
    kind: Literal["system_event", "agent_turn"] = "agent_turn"
    message: str = ""
    # 中文注释
    deliver: bool = False
    channel: str | None = None  # e.g. "whatsapp"
    to: str | None = None  # e.g. phone number


@dataclass
class CronJobState:
    """类说明：CronJobState。"""
    next_run_at_ms: int | None = None
    last_run_at_ms: int | None = None
    last_status: Literal["ok", "error", "skipped"] | None = None
    last_error: str | None = None


@dataclass
class CronJob:
    """类说明：CronJob。"""
    id: str
    name: str
    enabled: bool = True
    schedule: CronSchedule = field(default_factory=lambda: CronSchedule(kind="every"))
    payload: CronPayload = field(default_factory=CronPayload)
    state: CronJobState = field(default_factory=CronJobState)
    created_at_ms: int = 0
    updated_at_ms: int = 0
    delete_after_run: bool = False


@dataclass
class CronStore:
    """类说明：CronStore。"""
    version: int = 1
    jobs: list[CronJob] = field(default_factory=list)
