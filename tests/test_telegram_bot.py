from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "service_mvp" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from telegram_bot import (  # type: ignore[import-not-found]
    accept_telegram_order,
    extract_youtube_url,
    get_telegram_bot_token,
    send_delivery_to_telegram,
)
from order_store import read_orders  # type: ignore[import-not-found]
from case_manager import read_metadata  # type: ignore[import-not-found]


def test_get_telegram_bot_token_loads_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=test-token\n", encoding="utf-8")

    assert get_telegram_bot_token(env_file) == "test-token"


def test_extract_youtube_url_from_plain_or_mixed_text():
    assert extract_youtube_url("https://youtu.be/abc123") == "https://youtu.be/abc123"
    assert (
        extract_youtube_url("帮我处理这个视频：https://www.youtube.com/watch?v=abc123&t=30s 谢谢")
        == "https://www.youtube.com/watch?v=abc123&t=30s"
    )


def test_extract_youtube_url_rejects_non_youtube_text():
    assert extract_youtube_url("hello https://example.com/watch?v=abc123") is None
    assert extract_youtube_url("没有链接") is None


def test_accept_telegram_order_creates_case_and_order(tmp_path):
    cases_dir = tmp_path / "cases"
    orders_file = tmp_path / "tracking" / "orders.csv"

    result = accept_telegram_order(
        text="请处理 https://www.youtube.com/watch?v=abc123",
        chat_id=10001,
        message_id=42,
        username="alice",
        full_name="Alice Zhang",
        cases_dir=cases_dir,
        orders_file=orders_file,
        default_price_cny=0,
    )

    assert result.accepted is True
    assert result.order_id == "ord_tg_10001_42"
    assert result.case_id == "case_tg_10001_42"
    assert result.youtube_url == "https://www.youtube.com/watch?v=abc123"
    assert "ord_tg_10001_42" in result.reply_text
    assert "已收到" in result.reply_text

    case_dir = cases_dir / "case_tg_10001_42"
    assert (case_dir / "source_url.txt").read_text(encoding="utf-8").strip() == "https://www.youtube.com/watch?v=abc123"

    metadata = read_metadata(case_dir)
    assert metadata["source"] == "telegram"
    assert metadata["telegram_chat_id"] == "10001"
    assert metadata["telegram_message_id"] == "42"

    orders = read_orders(orders_file)
    assert len(orders) == 1
    assert orders[0]["order_id"] == "ord_tg_10001_42"
    assert orders[0]["customer_contact"] == "telegram:@alice"
    assert orders[0]["status"] == "new"
    assert orders[0]["price_cny"] == "0.00"


def test_send_delivery_to_telegram_sends_delivery_and_updates_metadata(tmp_path):
    cases_dir = tmp_path / "cases"
    orders_file = tmp_path / "tracking" / "orders.csv"
    order = accept_telegram_order(
        text="https://youtu.be/abc123",
        chat_id=10001,
        message_id=42,
        username="alice",
        full_name="Alice Zhang",
        cases_dir=cases_dir,
        orders_file=orders_file,
    )
    case_dir = Path(order.case_dir)
    (case_dir / "delivery.md").write_text("# 交付稿\n\n这是中文笔记。", encoding="utf-8")
    calls = []

    def fake_api(token, method, payload=None):
        calls.append((token, method, payload))
        return {"ok": True, "result": {"message_id": 777}}

    result = send_delivery_to_telegram(case_dir=case_dir, token="test-token", api_func=fake_api)

    assert result["ok"] is True
    assert result["chat_id"] == "10001"
    assert result["telegram_message_id"] == "777"
    assert calls == [
        (
            "test-token",
            "sendMessage",
            {
                "chat_id": "10001",
                "text": "# 交付稿\n\n这是中文笔记。",
                "disable_web_page_preview": True,
            },
        )
    ]
    metadata = read_metadata(case_dir)
    assert metadata["delivery_sent_to_telegram"] is True
    assert metadata["delivery_telegram_message_id"] == "777"


def test_send_delivery_to_telegram_requires_telegram_case(tmp_path):
    case_dir = tmp_path / "case_manual"
    case_dir.mkdir()
    (case_dir / "delivery.md").write_text("# 交付稿", encoding="utf-8")

    try:
        send_delivery_to_telegram(case_dir=case_dir, token="test-token")
    except ValueError as exc:
        assert "telegram_chat_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_accept_telegram_order_returns_help_for_missing_url(tmp_path):
    result = accept_telegram_order(
        text="你好",
        chat_id=10001,
        message_id=43,
        username="alice",
        full_name="Alice Zhang",
        cases_dir=tmp_path / "cases",
        orders_file=tmp_path / "orders.csv",
    )

    assert result.accepted is False
    assert result.order_id == ""
    assert "YouTube 链接" in result.reply_text
    assert not (tmp_path / "orders.csv").exists()
