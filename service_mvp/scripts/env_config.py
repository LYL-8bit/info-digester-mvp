from __future__ import annotations

import os
from pathlib import Path


def find_env_file(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents]
    script_root = Path(__file__).resolve().parents[2]
    candidates.append(script_root)

    for directory in candidates:
        env_path = directory / ".env"
        if env_path.exists():
            return env_path
    return None


def load_env(env_path: Path | None = None) -> dict[str, str]:
    path = env_path or find_env_file()
    values: dict[str, str] = {}
    if not path:
        return values

    for raw_line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        values[key] = value
        os.environ.setdefault(key, value)

    return values


def get_cookie_file() -> Path | None:
    load_env()
    raw_path = os.environ.get("YTDLP_COOKIE_FILE", "").strip()
    if not raw_path:
        return None
    return Path(raw_path).expanduser()


def cookie_status() -> tuple[Path | None, bool]:
    cookie_file = get_cookie_file()
    return cookie_file, bool(cookie_file and cookie_file.exists())
