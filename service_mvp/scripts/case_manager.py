from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CaseWorkspace:
    case_dir: Path
    source_url_file: Path
    transcript_file: Path
    prompt_file: Path
    note_file: Path
    delivery_file: Path
    metadata_file: Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_case_workspace(case_dir: Path) -> CaseWorkspace:
    return CaseWorkspace(
        case_dir=case_dir,
        source_url_file=case_dir / "source_url.txt",
        transcript_file=case_dir / "transcript.txt",
        prompt_file=case_dir / "prompt.txt",
        note_file=case_dir / "note.md",
        delivery_file=case_dir / "delivery.md",
        metadata_file=case_dir / "metadata.json",
    )


def read_metadata(case_dir: Path) -> dict[str, Any]:
    metadata_file = case_dir / "metadata.json"
    if not metadata_file.exists():
        return {}
    try:
        return json.loads(metadata_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_metadata(case_dir: Path, metadata: dict[str, Any]) -> None:
    metadata_file = case_dir / "metadata.json"
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    metadata_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def update_metadata(case_dir: Path, **updates: Any) -> dict[str, Any]:
    metadata = read_metadata(case_dir)
    metadata.update(updates)
    metadata["updated_at"] = _utc_now_iso()
    write_metadata(case_dir, metadata)
    return metadata


def ensure_case_workspace(case_dir: Path, youtube_url: str, case_title: str = "") -> CaseWorkspace:
    workspace = get_case_workspace(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    normalized_url = youtube_url.strip()
    if normalized_url:
        workspace.source_url_file.write_text(normalized_url + "\n", encoding="utf-8")

    if not workspace.note_file.exists():
        title = case_title.strip() or case_dir.name
        workspace.note_file.write_text(f"# {title}\n\n", encoding="utf-8")

    if not workspace.delivery_file.exists():
        workspace.delivery_file.write_text(
            "# 交付稿\n\n"
            "## 一句话总结\n\n"
            "## 是否值得看\n\n"
            "## 核心要点\n\n"
            "## 行动清单\n",
            encoding="utf-8",
        )

    existing = read_metadata(case_dir)
    metadata = {
        "case_id": case_dir.name,
        "case_title": case_title.strip(),
        "youtube_url": normalized_url,
        "status": existing.get("status", "created"),
        "created_at": existing.get("created_at", _utc_now_iso()),
        "updated_at": _utc_now_iso(),
    }
    for key, value in existing.items():
        metadata.setdefault(key, value)
    write_metadata(case_dir, metadata)
    return workspace


def save_prompt(case_dir: Path, prompt_text: str) -> Path:
    workspace = get_case_workspace(case_dir)
    workspace.prompt_file.write_text(prompt_text, encoding="utf-8")
    update_metadata(
        case_dir,
        prompt_chars=len(prompt_text),
        status="prompt_ready",
    )
    return workspace.prompt_file


def save_quality_checklist(case_dir: Path, checklist: dict[str, bool]) -> dict[str, Any]:
    return update_metadata(case_dir, quality_checklist=checklist)
