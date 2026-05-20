from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "service_mvp" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from ai_client import OpenAICompatibleConfig, chat_completion, get_ai_config  # type: ignore[import-not-found]


def test_get_ai_config_loads_openai_compatible_env(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_COMPATIBLE_BASE_URL=https://api.deepseek.com\n"
        "OPENAI_COMPATIBLE_API_KEY=test-key\n"
        "OPENAI_COMPATIBLE_MODEL=deepseek-chat\n",
        encoding="utf-8",
    )

    config = get_ai_config(env_file)

    assert config.base_url == "https://api.deepseek.com"
    assert config.api_key == "test-key"
    assert config.model == "deepseek-chat"


def test_chat_completion_posts_openai_compatible_payload():
    calls = []

    def fake_urlopen(request, timeout=60):
        calls.append((request, timeout))

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(
                    {"choices": [{"message": {"content": "# 中文笔记"}}]},
                    ensure_ascii=False,
                ).encode("utf-8")

        return Response()

    result = chat_completion(
        config=OpenAICompatibleConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            model="test-model",
        ),
        prompt="请总结",
        urlopen_func=fake_urlopen,
    )

    assert result == "# 中文笔记"
    request, timeout = calls[0]
    assert timeout == 120
    assert request.full_url == "https://api.example.com/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer test-key"
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["model"] == "test-model"
    assert payload["messages"][-1]["content"] == "请总结"
