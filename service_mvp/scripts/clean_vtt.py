from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+")
INDEX_RE = re.compile(r"^\d+$")
TAG_RE = re.compile(r"<[^>]+>")


def clean_vtt_text(text: str, dedupe: str = "adjacent") -> str:
    lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "WEBVTT":
            continue
        if line.startswith(("Kind:", "Language:", "NOTE", "STYLE", "REGION")):
            continue
        if "-->" in line or TIMESTAMP_RE.match(line):
            continue
        if INDEX_RE.match(line):
            continue

        line = TAG_RE.sub("", line)
        line = html.unescape(line).strip()
        if line:
            lines.append(line)

    if dedupe == "none":
        cleaned = lines
    elif dedupe == "global":
        seen: set[str] = set()
        cleaned = []
        for line in lines:
            if line not in seen:
                cleaned.append(line)
                seen.add(line)
    else:
        cleaned = []
        previous = None
        for line in lines:
            if line != previous:
                cleaned.append(line)
            previous = line

    return "\n".join(cleaned)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean a YouTube .vtt subtitle file into plain transcript text."
    )
    parser.add_argument("input", help="Path to the .vtt subtitle file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Output .txt path. Defaults to the input filename with .txt suffix.",
    )
    parser.add_argument(
        "--dedupe",
        choices=["adjacent", "global", "none"],
        default="adjacent",
        help="Deduplication mode. Use global for auto-caption files with repeated chunks.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".txt")

    text = input_path.read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_vtt_text(text, dedupe=args.dedupe)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(cleaned, encoding="utf-8")

    line_count = len([line for line in cleaned.splitlines() if line.strip()])
    print(f"Saved {line_count} lines to: {output_path}")


if __name__ == "__main__":
    main()

