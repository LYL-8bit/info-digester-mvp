from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ai_client import OpenAICompatibleConfig, chat_completion
from case_manager import ensure_case_workspace, save_prompt, update_metadata
from clean_vtt import clean_vtt_text
from env_config import cookie_status

SERVICE_ROOT = Path(__file__).resolve().parents[1]
PROMPT_FILE = SERVICE_ROOT / "02_固定Prompt.md"


@dataclass(frozen=True)
class AutoProcessResult:
    ok: bool
    case_dir: Path
    transcript_file: Path | None = None
    prompt_file: Path | None = None
    delivery_file: Path | None = None
    error: str = ""


def latest_vtt(case_dir: Path) -> Path | None:
    vtt_files = sorted(case_dir.glob("*.vtt"), key=lambda path: path.stat().st_mtime, reverse=True)
    return vtt_files[0] if vtt_files else None


def download_subtitle(
    youtube_url: str,
    output_dir: Path,
    lang: str = "en",
    use_auto_subs: bool = True,
) -> Path | None:
    if not shutil.which("yt-dlp"):
        raise RuntimeError("未找到 yt-dlp，请先安装依赖。")
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "yt-dlp",
        "--skip-download",
        "--sub-lang",
        lang,
        "--sub-format",
        "vtt",
        "--ignore-no-formats-error",
        "-o",
        str(output_dir / "%(title)s [%(id)s].%(ext)s"),
        "--write-auto-subs" if use_auto_subs else "--write-subs",
    ]
    cookie_file, has_cookie = cookie_status()
    if cookie_file and has_cookie:
        command.extend(["--cookies", str(cookie_file)])
    command.append(youtube_url)
    subprocess.run(command, cwd=SERVICE_ROOT.parent, capture_output=True, text=True, check=True)
    return latest_vtt(output_dir)


def build_prompt_from_template(transcript_text: str, prompt_file: Path = PROMPT_FILE) -> str:
    template = prompt_file.read_text(encoding="utf-8")
    placeholder = "在这里粘贴 transcript.txt"
    if placeholder in template:
        return template.replace(placeholder, transcript_text)
    return f"{template.rstrip()}\n\n```text\n{transcript_text}\n```"


def process_youtube_to_markdown(
    *,
    youtube_url: str,
    case_dir: Path,
    ai_config: OpenAICompatibleConfig,
    prompt_file: Path = PROMPT_FILE,
    lang: str = "en",
    download_func: Callable[..., Path | None] = download_subtitle,
    chat_func: Callable[[OpenAICompatibleConfig, str], str] | None = None,
) -> AutoProcessResult:
    ensure_case_workspace(case_dir, youtube_url=youtube_url, case_title="Telegram 自动生成")
    update_metadata(case_dir, status="auto_processing")

    try:
        vtt_file = download_func(youtube_url, case_dir, lang=lang, use_auto_subs=True)
        if not vtt_file:
            raise ValueError("未检测到可用字幕。")

        transcript_text = clean_vtt_text(vtt_file.read_text(encoding="utf-8", errors="ignore"), dedupe="adjacent")
        if not transcript_text.strip():
            raise ValueError("字幕清洗后为空。")
        transcript_file = case_dir / "transcript.txt"
        transcript_file.write_text(transcript_text, encoding="utf-8")

        prompt_text = build_prompt_from_template(transcript_text, prompt_file=prompt_file)
        saved_prompt_file = save_prompt(case_dir, prompt_text)

        generator = chat_func or (lambda config, prompt: chat_completion(config=config, prompt=prompt))
        note_text = generator(ai_config, prompt_text).strip()
        if not note_text:
            raise ValueError("AI 返回内容为空。")

        delivery_file = case_dir / "delivery.md"
        delivery_file.write_text(note_text + "\n", encoding="utf-8")
        update_metadata(
            case_dir,
            status="auto_delivered",
            auto_processor="openai_compatible",
            transcript_chars=len(transcript_text),
            prompt_chars=len(prompt_text),
            output_chars=len(note_text),
        )
        return AutoProcessResult(
            ok=True,
            case_dir=case_dir,
            transcript_file=transcript_file,
            prompt_file=saved_prompt_file,
            delivery_file=delivery_file,
        )
    except Exception as exc:
        update_metadata(case_dir, status="auto_failed", auto_error=str(exc))
        return AutoProcessResult(ok=False, case_dir=case_dir, error=str(exc))
