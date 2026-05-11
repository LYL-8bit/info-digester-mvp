from __future__ import annotations

import csv
import json
from pathlib import Path


TRACKING_DIR = Path(__file__).resolve().parents[1] / "tracking"
MAPPING_FILE = TRACKING_DIR / "字段映射.json"


def load_mapping() -> dict[str, dict[str, str]]:
    return json.loads(MAPPING_FILE.read_text(encoding="utf-8"))


def reverse_mapping(chinese_to_english: dict[str, str]) -> dict[str, str]:
    return {english: chinese for chinese, english in chinese_to_english.items()}


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def migrate_file(path: Path, chinese_to_english: dict[str, str]) -> None:
    english_to_chinese = reverse_mapping(chinese_to_english)
    chinese_headers = list(chinese_to_english.keys())
    rows = read_rows(path)

    normalized_rows: list[dict[str, str]] = []
    for row in rows:
        normalized: dict[str, str] = {}
        for chinese_header in chinese_headers:
            english_header = chinese_to_english[chinese_header]
            normalized[chinese_header] = row.get(chinese_header, row.get(english_header, ""))
        normalized_rows.append(normalized)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=chinese_headers)
        writer.writeheader()
        writer.writerows(normalized_rows)


def main() -> None:
    mapping = load_mapping()
    for filename, chinese_to_english in mapping.items():
        migrate_file(TRACKING_DIR / filename, chinese_to_english)
        print(f"Migrated: {filename}")


if __name__ == "__main__":
    main()
