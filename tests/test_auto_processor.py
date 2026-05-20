from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "service_mvp" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from ai_client import OpenAICompatibleConfig  # type: ignore[import-not-found]
from auto_processor import process_youtube_to_markdown  # type: ignore[import-not-found]
from case_manager import read_metadata  # type: ignore[import-not-found]


def test_process_youtube_to_markdown_creates_artifacts(tmp_path):
    prompt_template = tmp_path / "prompt.md"
    prompt_template.write_text("请整理字幕：\n在这里粘贴 transcript.txt", encoding="utf-8")
    case_dir = tmp_path / "case_auto"

    def fake_download(url, output_dir, lang="en", use_auto_subs=True):
        vtt = output_dir / "demo.en.vtt"
        vtt.parent.mkdir(parents=True, exist_ok=True)
        vtt.write_text(
            "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello world\n",
            encoding="utf-8",
        )
        return vtt

    def fake_chat(config, prompt):
        assert "Hello world" in prompt
        return "# 中文笔记\n\n你好世界"

    result = process_youtube_to_markdown(
        youtube_url="https://youtu.be/abc123",
        case_dir=case_dir,
        ai_config=OpenAICompatibleConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            model="test-model",
        ),
        prompt_file=prompt_template,
        download_func=fake_download,
        chat_func=fake_chat,
    )

    assert result.ok is True
    assert result.delivery_file == case_dir / "delivery.md"
    assert (case_dir / "transcript.txt").read_text(encoding="utf-8") == "Hello world"
    assert "Hello world" in (case_dir / "prompt.txt").read_text(encoding="utf-8")
    assert (case_dir / "delivery.md").read_text(encoding="utf-8") == "# 中文笔记\n\n你好世界\n"
    metadata = read_metadata(case_dir)
    assert metadata["status"] == "auto_delivered"
    assert metadata["auto_processor"] == "openai_compatible"


def test_process_youtube_to_markdown_fails_when_no_subtitle(tmp_path):
    def fake_download(url, output_dir, lang="en", use_auto_subs=True):
        return None

    result = process_youtube_to_markdown(
        youtube_url="https://youtu.be/abc123",
        case_dir=tmp_path / "case_auto",
        ai_config=OpenAICompatibleConfig(base_url="https://api.example.com", api_key="key", model="model"),
        prompt_file=tmp_path / "missing.md",
        download_func=fake_download,
        chat_func=lambda config, prompt: "never",
    )

    assert result.ok is False
    assert "字幕" in result.error
