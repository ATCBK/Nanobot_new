"""模块说明：helpers。"""

from pathlib import Path
from datetime import datetime


def ensure_dir(path: Path) -> Path:
    """函数说明：ensure_dir。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_path() -> Path:
    """函数说明：get_data_path。"""
    return ensure_dir(Path.home() / ".nanobot")


def get_workspace_path(workspace: str | None = None) -> Path:
    """函数说明：get_workspace_path。"""
    if workspace:
        path = Path(workspace).expanduser()
    else:
        path = Path.home() / ".nanobot" / "workspace"
    return ensure_dir(path)


def get_sessions_path() -> Path:
    """函数说明：get_sessions_path。"""
    return ensure_dir(get_data_path() / "sessions")


def get_memory_path(workspace: Path | None = None) -> Path:
    """函数说明：get_memory_path。"""
    ws = workspace or get_workspace_path()
    return ensure_dir(ws / "memory")


def get_skills_path(workspace: Path | None = None) -> Path:
    """函数说明：get_skills_path。"""
    ws = workspace or get_workspace_path()
    return ensure_dir(ws / "skills")


def today_date() -> str:
    """函数说明：today_date。"""
    return datetime.now().strftime("%Y-%m-%d")


def timestamp() -> str:
    """函数说明：timestamp。"""
    return datetime.now().isoformat()


def truncate_string(s: str, max_len: int = 100, suffix: str = "...") -> str:
    """函数说明：truncate_string。"""
    if len(s) <= max_len:
        return s
    return s[: max_len - len(suffix)] + suffix


def safe_filename(name: str) -> str:
    """函数说明：safe_filename。"""
    # 中文注释
    unsafe = '<>:"/\\|?*'
    for char in unsafe:
        name = name.replace(char, "_")
    return name.strip()


def parse_session_key(key: str) -> tuple[str, str]:
    """函数说明：parse_session_key。"""
    parts = key.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid session key: {key}")
    return parts[0], parts[1]
