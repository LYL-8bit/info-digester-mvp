from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from case_manager import ensure_case_workspace, read_metadata, update_metadata
from env_config import load_env
from order_store import order_id_from_case_id, save_order

SERVICE_ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = SERVICE_ROOT / "cases"
ORDERS_FILE = SERVICE_ROOT / "tracking" / "orders.csv"

YOUTUBE_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?[^\s]+|shorts/[^\s]+|live/[^\s]+)|youtu\.be/[^\s]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TelegramOrderResult:
    accepted: bool
    reply_text: str
    order_id: str = ""
    case_id: str = ""
    youtube_url: str = ""
    case_dir: str = ""


def extract_youtube_url(text: str) -> str | None:
    match = YOUTUBE_URL_RE.search(text or "")
    if not match:
        return None
    return match.group(0).rstrip("，。,.!！?？)）]")


def get_telegram_bot_token(env_path: Path | None = None) -> str:
    load_env(env_path)
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def _telegram_contact(username: str, chat_id: int | str) -> str:
    value = (username or "").strip().lstrip("@")
    if value:
        return f"telegram:@{value}"
    return f"telegram:{chat_id}"


def _telegram_customer_name(full_name: str, username: str, chat_id: int | str) -> str:
    if full_name.strip():
        return full_name.strip()
    if username.strip():
        return username.strip().lstrip("@")
    return f"telegram_user_{chat_id}"


def accept_telegram_order(
    *,
    text: str,
    chat_id: int | str,
    message_id: int | str,
    username: str = "",
    full_name: str = "",
    cases_dir: Path = CASES_DIR,
    orders_file: Path = ORDERS_FILE,
    default_price_cny: float = 0.0,
) -> TelegramOrderResult:
    youtube_url = extract_youtube_url(text)
    if not youtube_url:
        return TelegramOrderResult(
            accepted=False,
            reply_text="请直接发送一个 YouTube 链接，例如：https://www.youtube.com/watch?v=VIDEO_ID",
        )

    case_id = f"case_tg_{chat_id}_{message_id}"
    case_dir = cases_dir / case_id
    order_id = order_id_from_case_id(case_id)

    ensure_case_workspace(case_dir, youtube_url=youtube_url, case_title="Telegram 体验单")
    update_metadata(
        case_dir,
        source="telegram",
        telegram_chat_id=str(chat_id),
        telegram_message_id=str(message_id),
        telegram_username=username.strip().lstrip("@"),
    )

    save_order(
        orders_file=orders_file,
        order_id=order_id,
        customer_name=_telegram_customer_name(full_name, username, chat_id),
        customer_contact=_telegram_contact(username, chat_id),
        youtube_url=youtube_url,
        case_id=case_id,
        case_title="Telegram 体验单",
        price_cny=default_price_cny,
        status="new",
        case_dir=str(case_dir),
    )

    reply = (
        "已收到 YouTube 链接。\n"
        f"订单号：{order_id}\n"
        f"案例编号：{case_id}\n"
        "当前状态：已进入待处理队列。"
    )
    return TelegramOrderResult(
        accepted=True,
        reply_text=reply,
        order_id=order_id,
        case_id=case_id,
        youtube_url=youtube_url,
        case_dir=str(case_dir),
    )


def _telegram_api(token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(request, timeout=60) as response:  # nosec: Telegram Bot API endpoint
        return json.loads(response.read().decode("utf-8"))


def send_delivery_to_telegram(
    *,
    case_dir: Path,
    token: str,
    api_func: Any = None,
) -> dict[str, str | bool]:
    metadata = read_metadata(case_dir)
    chat_id = str(metadata.get("telegram_chat_id", "")).strip()
    if not chat_id:
        raise ValueError("metadata.json 缺少 telegram_chat_id，无法发送给 Telegram 用户。")

    delivery_file = case_dir / "delivery.md"
    if not delivery_file.exists():
        raise ValueError(f"交付稿不存在：{delivery_file}")
    delivery_text = delivery_file.read_text(encoding="utf-8", errors="ignore").strip()
    if not delivery_text:
        raise ValueError(f"交付稿为空：{delivery_file}")
    if len(delivery_text) > 3900:
        raise ValueError("交付稿超过 Telegram 单条文本安全长度，请先缩短或后续改为文件发送。")

    api = api_func or _telegram_api
    response = api(
        token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": delivery_text,
            "disable_web_page_preview": True,
        },
    )
    message_id = str((response.get("result") or {}).get("message_id", ""))
    update_metadata(
        case_dir,
        delivery_sent_to_telegram=True,
        delivery_telegram_message_id=message_id,
    )
    return {"ok": bool(response.get("ok")), "chat_id": chat_id, "telegram_message_id": message_id}


def _handle_update(token: str, update: dict[str, Any], *, cases_dir: Path, orders_file: Path) -> int | None:
    message = update.get("message") or update.get("edited_message") or {}
    text = message.get("text") or ""
    chat = message.get("chat") or {}
    from_user = message.get("from") or {}
    chat_id = chat.get("id")
    message_id = message.get("message_id")
    if chat_id is None or message_id is None:
        return update.get("update_id")

    full_name = " ".join(
        part for part in [from_user.get("first_name", ""), from_user.get("last_name", "")] if part
    )
    result = accept_telegram_order(
        text=text,
        chat_id=chat_id,
        message_id=message_id,
        username=from_user.get("username", ""),
        full_name=full_name,
        cases_dir=cases_dir,
        orders_file=orders_file,
    )
    _telegram_api(token, "sendMessage", {"chat_id": chat_id, "text": result.reply_text})
    return update.get("update_id")


def run_polling(
    *,
    token: str,
    cases_dir: Path = CASES_DIR,
    orders_file: Path = ORDERS_FILE,
    poll_interval_seconds: float = 1.0,
) -> None:
    offset = 0
    while True:
        response = _telegram_api(token, "getUpdates", {"offset": offset, "timeout": 30})
        for update in response.get("result", []):
            update_id = _handle_update(token, update, cases_dir=cases_dir, orders_file=orders_file)
            if update_id is not None:
                offset = max(offset, int(update_id) + 1)
        time.sleep(poll_interval_seconds)


def main() -> None:
    token = get_telegram_bot_token()
    if not token:
        raise SystemExit("请先设置 TELEGRAM_BOT_TOKEN 环境变量，或写入项目根目录 .env。")
    run_polling(token=token)


if __name__ == "__main__":
    main()
