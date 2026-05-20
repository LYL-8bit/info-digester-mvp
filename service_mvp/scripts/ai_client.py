from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from env_config import load_env


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.2
    max_tokens: int = 4096


def get_ai_config(env_path: Path | None = None) -> OpenAICompatibleConfig:
    load_env(env_path)
    return OpenAICompatibleConfig(
        base_url=os.environ.get("OPENAI_COMPATIBLE_BASE_URL", "").strip().rstrip("/"),
        api_key=os.environ.get("OPENAI_COMPATIBLE_API_KEY", "").strip(),
        model=os.environ.get("OPENAI_COMPATIBLE_MODEL", "deepseek-chat").strip() or "deepseek-chat",
        temperature=float(os.environ.get("OPENAI_COMPATIBLE_TEMPERATURE", "0.2") or "0.2"),
        max_tokens=int(os.environ.get("OPENAI_COMPATIBLE_MAX_TOKENS", "4096") or "4096"),
    )


def ensure_ai_config(config: OpenAICompatibleConfig) -> None:
    if not config.base_url:
        raise ValueError("缺少 OPENAI_COMPATIBLE_BASE_URL。")
    if not config.api_key:
        raise ValueError("缺少 OPENAI_COMPATIBLE_API_KEY。")
    if not config.model:
        raise ValueError("缺少 OPENAI_COMPATIBLE_MODEL。")


def chat_completion(
    *,
    config: OpenAICompatibleConfig,
    prompt: str,
    system_prompt: str = "你是一个中文知识整理助手。请输出结构清晰、可直接保存为 Markdown 的中文笔记。",
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
) -> str:
    ensure_ai_config(config)
    url = f"{config.base_url}/v1/chat/completions"
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )
    with urlopen_func(request, timeout=120) as response:
        body = json.loads(response.read().decode("utf-8"))
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"AI API 返回格式异常：{body}") from exc
    return str(content).strip()
