from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "service_mvp" / "scripts"))

from clean_vtt import clean_vtt_text  # type: ignore[import-not-found]


def test_clean_vtt_removes_headers_timestamps_tags_and_indexes():
    raw = """WEBVTT
Kind: captions
Language: en

1
00:00:00.000 --> 00:00:02.000
<v Speaker>Hello &amp; welcome</v>

2
00:00:02.000 --> 00:00:04.000
<b>to Codex</b>
"""

    assert clean_vtt_text(raw) == "Hello & welcome\nto Codex"


def test_clean_vtt_adjacent_dedupe_only_removes_neighbor_duplicates():
    raw = """WEBVTT

hello
hello
world
hello
"""

    assert clean_vtt_text(raw, dedupe="adjacent") == "hello\nworld\nhello"


def test_clean_vtt_global_dedupe_removes_all_repeated_lines():
    raw = """WEBVTT

hello
hello
world
hello
"""

    assert clean_vtt_text(raw, dedupe="global") == "hello\nworld"


def test_clean_vtt_none_keeps_duplicates():
    raw = """WEBVTT

hello
hello
"""

    assert clean_vtt_text(raw, dedupe="none") == "hello\nhello"
