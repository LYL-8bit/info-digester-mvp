from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "service_mvp" / "scripts"))

from case_manager import ensure_case_workspace, save_prompt, save_quality_checklist  # type: ignore[import-not-found]


def test_ensure_case_workspace_creates_standard_files(tmp_path):
    case_dir = tmp_path / "case_20260520_demo"

    workspace = ensure_case_workspace(
        case_dir=case_dir,
        youtube_url="https://www.youtube.com/watch?v=abc123",
        case_title="Demo Video",
    )

    assert workspace.case_dir == case_dir
    assert (case_dir / "source_url.txt").read_text(encoding="utf-8") == "https://www.youtube.com/watch?v=abc123\n"
    assert (case_dir / "note.md").read_text(encoding="utf-8").startswith("# Demo Video")
    assert (case_dir / "delivery.md").exists()
    assert (case_dir / "metadata.json").exists()

    metadata = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["case_title"] == "Demo Video"
    assert metadata["youtube_url"] == "https://www.youtube.com/watch?v=abc123"
    assert metadata["status"] == "created"


def test_ensure_case_workspace_does_not_overwrite_existing_note(tmp_path):
    case_dir = tmp_path / "case_existing"
    case_dir.mkdir()
    note = case_dir / "note.md"
    note.write_text("# Existing\n\nkeep me", encoding="utf-8")

    ensure_case_workspace(case_dir=case_dir, youtube_url="https://youtu.be/x", case_title="New")

    assert note.read_text(encoding="utf-8") == "# Existing\n\nkeep me"


def test_save_prompt_writes_prompt_and_updates_metadata(tmp_path):
    case_dir = tmp_path / "case_prompt"
    ensure_case_workspace(case_dir=case_dir, youtube_url="https://youtu.be/x", case_title="Prompt")

    save_prompt(case_dir, "PROMPT BODY")

    assert (case_dir / "prompt.txt").read_text(encoding="utf-8") == "PROMPT BODY"
    metadata = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["prompt_chars"] == 11
    assert metadata["status"] == "prompt_ready"


def test_save_quality_checklist_updates_metadata(tmp_path):
    case_dir = tmp_path / "case_quality"
    ensure_case_workspace(case_dir=case_dir, youtube_url="https://youtu.be/x", case_title="Quality")

    save_quality_checklist(case_dir, {"no_fake_timestamps": True, "markdown_ok": False})

    metadata = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["quality_checklist"] == {"no_fake_timestamps": True, "markdown_ok": False}
