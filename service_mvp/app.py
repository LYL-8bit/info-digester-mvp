from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


SERVICE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = SERVICE_ROOT.parent
SCRIPTS_DIR = SERVICE_ROOT / "scripts"
CASES_DIR = SERVICE_ROOT / "cases"
PROMPT_FILE = SERVICE_ROOT / "02_固定Prompt.md"
TRACKING_DIR = SERVICE_ROOT / "tracking"
ORDERS_FILE = TRACKING_DIR / "orders.csv"

sys.path.insert(0, str(SCRIPTS_DIR))

from case_manager import ensure_case_workspace, save_prompt, save_quality_checklist  # type: ignore[import-not-found]  # noqa: E402
from clean_vtt import clean_vtt_text  # noqa: E402
from env_config import cookie_status  # noqa: E402
from order_store import order_id_from_case_id, save_order, summarize_orders, update_order_status  # type: ignore[import-not-found]  # noqa: E402


def sanitize_case_id(raw_case_id: str) -> str:
    value = raw_case_id.strip()
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", value)
    if not value:
        value = "case_001"
    if not value.startswith("case_"):
        value = f"case_{value}"
    return value


def run_command(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        return False, str(exc)

    output = "\n".join(part for part in [result.stdout, result.stderr] if part)
    return result.returncode == 0, output.strip()


def add_cookie_args(command: list[str], use_cookies: bool) -> list[str]:
    cookie_file, has_cookie = cookie_status()
    if use_cookies and has_cookie and cookie_file:
        command.extend(["--cookies", str(cookie_file)])
    return command


def build_list_subs_command(youtube_url: str, use_cookies: bool) -> list[str]:
    command = ["yt-dlp", "--skip-download", "--list-subs"]
    add_cookie_args(command, use_cookies)
    command.append(youtube_url)
    return command


def build_download_command(
    youtube_url: str,
    case_dir: Path,
    use_cookies: bool,
    use_auto_subs: bool,
    lang: str,
) -> list[str]:
    command = [
        "yt-dlp",
        "--skip-download",
        "--sub-lang",
        lang,
        "--sub-format",
        "vtt",
        "--ignore-no-formats-error",
        "-o",
        str(case_dir / "%(title)s [%(id)s].%(ext)s"),
    ]

    command.append("--write-auto-subs" if use_auto_subs else "--write-subs")

    add_cookie_args(command, use_cookies)

    command.append(youtube_url)
    return command


def diagnose_yt_dlp_output(output: str) -> list[str]:
    hints: list[str] = []
    lower_output = output.lower()

    if "only images are available" in lower_output or "requested format is not available" in lower_output:
        hints.append(
            "这个链接当前没有可用的视频/字幕格式，常见于直播未结束、回放未处理完成、会员/年龄/地区限制，或 YouTube 暂时只暴露缩略图。"
        )
    if "n challenge solving failed" in lower_output:
        hints.append(
            "YouTube 的 n challenge 解析失败。通常不影响字幕优先尝试，但如果一直失败，可以更新 yt-dlp，或安装 Node.js 后再试。"
        )
    if "there are no subtitles" in lower_output or "no subtitles" in lower_output:
        hints.append("这个视频没有检测到目标语言字幕。可以切换字幕语言，或等直播回放处理完成后再试。")
    if "sign in" in lower_output or "cookies" in lower_output:
        hints.append("这个视频可能需要登录态。请确认 .env 中的 cookie 文件是最新导出的。")

    return hints


def latest_vtt(case_dir: Path) -> Path | None:
    vtt_files = sorted(case_dir.glob("*.vtt"), key=lambda path: path.stat().st_mtime, reverse=True)
    return vtt_files[0] if vtt_files else None


def clean_subtitle(vtt_file: Path, output_file: Path, dedupe: str) -> str:
    text = vtt_file.read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_vtt_text(text, dedupe=dedupe)
    output_file.write_text(cleaned, encoding="utf-8")
    return cleaned


def build_prompt(transcript_text: str) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    placeholder = "在这里粘贴 transcript.txt"
    if placeholder in template:
        return template.replace(placeholder, transcript_text)
    return f"{template.rstrip()}\n\n```text\n{transcript_text}\n```"


def text_char_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore"))


def render_copy_button(text: str, label: str = "复制完整 Prompt") -> None:
    text_json = json.dumps(text, ensure_ascii=False)
    components.html(
        f"""
        <button id="copyPromptButton" style="
            padding: 0.55rem 0.85rem;
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 0.5rem;
            background: #ffffff;
            color: #111827;
            cursor: pointer;
            font-weight: 600;
        ">{label}</button>
        <span id="copyPromptStatus" style="margin-left: 0.75rem; color: #16a34a; font-size: 0.9rem;"></span>
        <script>
        const promptText = {text_json};
        const button = document.getElementById("copyPromptButton");
        const status = document.getElementById("copyPromptStatus");
        button.addEventListener("click", async () => {{
            try {{
                await navigator.clipboard.writeText(promptText);
                status.textContent = "已复制";
            }} catch (error) {{
                const textarea = document.createElement("textarea");
                textarea.value = promptText;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                document.execCommand("copy");
                document.body.removeChild(textarea);
                status.textContent = "已复制";
            }}
            window.setTimeout(() => {{
                status.textContent = "";
            }}, 2200);
        }});
        </script>
        """,
        height=48,
    )


st.set_page_config(page_title="信息消化器接单操作台", page_icon="BP", layout="wide")

st.title("信息消化器接单操作台")
st.caption("本地使用：下载英文字幕、清洗 transcript、生成可复制 Prompt。")

summary = summarize_orders(ORDERS_FILE)
st.subheader("收入仪表盘")
metric_cols = st.columns(6)
metric_cols[0].metric("总订单", summary["total_orders"])
metric_cols[1].metric("已付款", summary["paid_orders"])
metric_cols[2].metric("已交付", summary["delivered_orders"])
metric_cols[3].metric("总收入 RMB", summary["revenue_cny"])
metric_cols[4].metric("估算利润 RMB", summary["estimated_profit_cny"])
metric_cols[5].metric("距 $40 成本还差 RMB", summary["token_budget_gap_cny"])
st.progress(float(summary["token_budget_progress_pct"]) / 100)
st.caption(
    f"Token 成本目标：{summary['token_budget_cny']} RMB / 月；"
    f"当前完成度：{summary['token_budget_progress_pct']}%；"
    f"已取消订单：{summary['cancelled_orders']}。"
)

cookie_file, has_cookie = cookie_status()
cookie_label = "已找到" if has_cookie else "未找到"
st.info(f"Cookie 状态：{cookie_label}")

with st.sidebar:
    st.header("订单信息")
    customer_name = st.text_input("客户名称", value="")
    customer_contact = st.text_input("客户联系方式", value="")
    price_cny = st.number_input("成交价格 / 元", min_value=0.0, value=19.9, step=1.0)
    order_status = st.selectbox("订单状态", ["new", "paid", "processing", "delivered", "cancelled"], index=0)
    youtube_url = st.text_input("YouTube 链接")
    case_id = sanitize_case_id(st.text_input("案例编号", value="case_003"))
    case_title = st.text_input("案例标题", value="")
    lang = st.text_input("字幕语言", value="en")
    use_cookies = st.checkbox("使用 .env 中的 cookie", value=True)
    use_auto_subs = st.checkbox("下载自动字幕", value=True)
    dedupe = st.selectbox("清洗去重方式", ["adjacent", "global", "none"], index=0)

case_dir = CASES_DIR / case_id
transcript_file = case_dir / "transcript.txt"
note_file = case_dir / "note.md"
prompt_file = case_dir / "prompt.txt"
metadata_file = case_dir / "metadata.json"
order_id = order_id_from_case_id(case_id)

st.subheader("1. 创建案例目录")
st.code(str(case_dir), language="text")
if st.button("创建/确认案例目录"):
    ensure_case_workspace(case_dir, youtube_url=youtube_url, case_title=case_title)
    st.success("案例目录已就绪，已保存 source_url.txt / note.md / delivery.md / metadata.json。")
    st.code(
        "\n".join(
            [
                str(case_dir / "source_url.txt"),
                str(transcript_file),
                str(prompt_file),
                str(note_file),
                str(case_dir / "delivery.md"),
                str(metadata_file),
            ]
        ),
        language="text",
    )

st.subheader("1.5 保存/更新订单记录")
st.caption(f"订单 ID：`{order_id}`；订单表：`{ORDERS_FILE}`")
if st.button("保存/更新订单"):
    if not youtube_url.strip():
        st.error("请先输入 YouTube 链接。")
    else:
        ensure_case_workspace(case_dir, youtube_url=youtube_url, case_title=case_title)
        saved_order = save_order(
            orders_file=ORDERS_FILE,
            order_id=order_id,
            customer_name=customer_name,
            customer_contact=customer_contact,
            youtube_url=youtube_url,
            case_id=case_id,
            case_title=case_title,
            price_cny=float(price_cny),
            status=order_status,
            case_dir=str(case_dir),
            transcript_chars=text_char_count(transcript_file),
            prompt_chars=text_char_count(prompt_file),
            output_chars=text_char_count(note_file) + text_char_count(case_dir / "delivery.md"),
        )
        st.success("订单已保存。")
        st.json(saved_order)

if st.button("标记为已交付"):
    try:
        delivered_order = update_order_status(ORDERS_FILE, order_id, "delivered")
        st.success("订单已标记为 delivered。")
        st.json(delivered_order)
    except ValueError as exc:
        st.error(str(exc))

st.subheader("2. 下载英文字幕")
if not shutil.which("yt-dlp"):
    st.warning("未在 PATH 中找到 yt-dlp。请先确认 yt-dlp 已安装。")

if use_cookies and not has_cookie:
    st.warning("已选择使用 cookie，但 .env 中的 cookie 文件未找到。下载时将不使用 cookie。")

if st.button("检查可用字幕"):
    if not youtube_url.strip():
        st.error("请先输入 YouTube 链接。")
    else:
        command = build_list_subs_command(youtube_url.strip(), use_cookies=use_cookies)
        ok, output = run_command(command)
        st.code(output or "yt-dlp finished.", language="text")
        hints = diagnose_yt_dlp_output(output)
        for hint in hints:
            st.warning(hint)
        if ok and not hints:
            st.success("字幕列表检查完成。")

if st.button("下载字幕"):
    if not youtube_url.strip():
        st.error("请先输入 YouTube 链接。")
    else:
        ensure_case_workspace(case_dir, youtube_url=youtube_url, case_title=case_title)
        command = build_download_command(
            youtube_url=youtube_url.strip(),
            case_dir=case_dir,
            use_cookies=use_cookies,
            use_auto_subs=use_auto_subs,
            lang=lang.strip() or "en",
        )
        ok, output = run_command(command)
        st.code(output or "yt-dlp finished.", language="text")
        hints = diagnose_yt_dlp_output(output)
        for hint in hints:
            st.warning(hint)
        if ok:
            st.success("字幕下载命令已完成。")
        else:
            st.error("字幕下载失败，请查看输出。")

st.subheader("3. 清洗字幕")
vtt_file = latest_vtt(case_dir) if case_dir.exists() else None
if vtt_file:
    st.write(f"检测到字幕文件：`{vtt_file.name}`")
else:
    st.write("尚未检测到 `.vtt` 字幕文件。")

if st.button("清洗为 transcript.txt"):
    if not vtt_file:
        st.error("没有找到 `.vtt` 字幕文件。")
    else:
        transcript_text = clean_subtitle(vtt_file, transcript_file, dedupe=dedupe)
        line_count = len([line for line in transcript_text.splitlines() if line.strip()])
        st.success(f"已生成 transcript.txt，共 {line_count} 行。")

st.subheader("4. 复制 Prompt 到 ChatGPT / Claude")
if transcript_file.exists():
    transcript_text = transcript_file.read_text(encoding="utf-8", errors="ignore")
    complete_prompt = build_prompt(transcript_text)
    save_prompt(prompt_text=complete_prompt, case_dir=case_dir)
    st.success(f"已保存完整 Prompt：{prompt_file}")
    render_copy_button(complete_prompt)
    st.download_button(
        "下载完整 Prompt.txt",
        complete_prompt,
        file_name=f"{case_id}_prompt.txt",
        mime="text/plain",
    )
    st.text_area("完整 Prompt", complete_prompt, height=360)
else:
    st.write("生成 `transcript.txt` 后，这里会出现完整 Prompt。")

st.subheader("5. 交付检查")
quality_checklist = {
    "summary_under_60_chars": st.checkbox("一句话总结不超过 60 字"),
    "has_clear_watch_judgement": st.checkbox("是否值得看有明确判断"),
    "no_fake_timestamps": st.checkbox("没有编造时间戳"),
    "no_fake_commands": st.checkbox("没有编造命令"),
    "markdown_table_ok": st.checkbox("Markdown 表格正常"),
    "ready_for_obsidian_notion_wechat": st.checkbox("可以直接复制到 Obsidian / Notion / 微信"),
}
if st.button("保存交付检查结果"):
    if not case_dir.exists():
        st.error("请先创建案例目录。")
    else:
        save_quality_checklist(case_dir, quality_checklist)
        st.success(f"已保存到 metadata.json：{metadata_file}")

st.subheader("6. 小红书发布提醒")
st.markdown(
    """
- 第一张图：封面标题。
- 第二张图：原视频截图。
- 第三张图：一句话总结 + 是否值得看。
- 第四张图：核心观点。
- 第五张图：技术步骤 / 行动清单。
"""
)
