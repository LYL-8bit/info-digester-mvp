from pathlib import Path
import re

vtt_file = Path(r"D:\MVP\This is ChatGPT Images 2.0 [-7JSa_luc6k].en.vtt")
out_file = Path(r"D:\MVP\transcript 1.txt")

text = vtt_file.read_text(encoding="utf-8", errors="ignore")

lines = []
for line in text.splitlines():
    line = line.strip()
    if not line:                              # 过滤空行和单空格占位行
        continue
    if line == "WEBVTT":
        continue
    if "-->" in line:
        continue
    if line.startswith(("Kind:", "Language:")):
        continue
    if re.match(r"^\d+$", line):
        continue

    line = re.sub(r"<[^>]+>", "", line)      # 去除所有 HTML/VTT 标签
    line = re.sub(r"&amp;", "&", line)
    line = re.sub(r"&lt;", "<", line)
    line = re.sub(r"&gt;", ">", line)
    line = line.strip()                       # 标签移除后可能产生新的首尾空格

    if not line:                              # 标签移除后可能变成空行
        continue

    lines.append(line)

# ✅ 改进：使用 seen 集合做全局去重，而非仅相邻去重
seen = set()
cleaned = []
for line in lines:
    if line not in seen:
        cleaned.append(line)
        seen.add(line)

out_file.write_text("\n".join(cleaned), encoding="utf-8")
print(f"Saved to: {out_file}")