from pathlib import Path
import re

vtt_file = Path(r"D:\MVP\Codex can now use Chrome directly on macOS and Windows. [b6Mxcv1pyBU].en.vtt")
out_file = Path(r"D:\MVP\transcript.txt")

text = vtt_file.read_text(encoding="utf-8", errors="ignore")

lines = []
for line in text.splitlines():
    line = line.strip()

    if not line:
        continue
    if line == "WEBVTT":
        continue
    if "-->" in line:
        continue
    if line.startswith(("Kind:", "Language:")):
        continue
    if re.match(r"^\d+$", line):
        continue

    line = re.sub(r"<[^>]+>", "", line)
    line = re.sub(r"&amp;", "&", line)
    line = re.sub(r"&lt;", "<", line)
    line = re.sub(r"&gt;", ">", line)

    lines.append(line)

# 简单去重：避免 YouTube 自动字幕重复片段
cleaned = []
prev = None
for line in lines:
    if line != prev:
        cleaned.append(line)
    prev = line

out_file.write_text("\n".join(cleaned), encoding="utf-8")

print(f"Saved to: {out_file}")