from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "service_mvp" / "scripts"))

from order_store import (  # type: ignore[import-not-found]
    estimate_order_metrics,
    order_id_from_case_id,
    save_order,
    update_order_status,
)


def read_orders(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_order_id_from_case_id_is_stable_and_prefixed():
    assert order_id_from_case_id("case_20260520_demo") == "ord_20260520_demo"


def test_save_order_creates_csv_with_header_and_order(tmp_path):
    orders_file = tmp_path / "orders.csv"

    saved = save_order(
        orders_file=orders_file,
        order_id="ord_demo",
        customer_name="张三",
        customer_contact="wx-demo",
        youtube_url="https://youtu.be/demo",
        case_id="case_demo",
        case_title="Demo",
        price_cny=19.9,
        status="new",
        case_dir="service_mvp/cases/case_demo",
        transcript_chars=1000,
        prompt_chars=2000,
    )

    rows = read_orders(orders_file)
    assert len(rows) == 1
    assert rows[0]["order_id"] == "ord_demo"
    assert rows[0]["customer_name"] == "张三"
    assert rows[0]["price_cny"] == "19.90"
    assert rows[0]["status"] == "new"
    assert rows[0]["estimated_profit_cny"] == saved["estimated_profit_cny"]


def test_save_order_upserts_existing_order(tmp_path):
    orders_file = tmp_path / "orders.csv"

    save_order(
        orders_file=orders_file,
        order_id="ord_demo",
        customer_name="张三",
        customer_contact="wx-old",
        youtube_url="https://youtu.be/old",
        case_id="case_demo",
        case_title="Old",
        price_cny=9.9,
        status="new",
        case_dir="cases/old",
    )
    save_order(
        orders_file=orders_file,
        order_id="ord_demo",
        customer_name="李四",
        customer_contact="wx-new",
        youtube_url="https://youtu.be/new",
        case_id="case_demo",
        case_title="New",
        price_cny=29.9,
        status="paid",
        case_dir="cases/new",
    )

    rows = read_orders(orders_file)
    assert len(rows) == 1
    assert rows[0]["customer_name"] == "李四"
    assert rows[0]["price_cny"] == "29.90"
    assert rows[0]["status"] == "paid"


def test_update_order_status_sets_delivered_at_for_delivered(tmp_path):
    orders_file = tmp_path / "orders.csv"
    save_order(
        orders_file=orders_file,
        order_id="ord_demo",
        customer_name="张三",
        customer_contact="wx-demo",
        youtube_url="https://youtu.be/demo",
        case_id="case_demo",
        case_title="Demo",
        price_cny=19.9,
        status="paid",
        case_dir="cases/demo",
    )

    update_order_status(orders_file, "ord_demo", "delivered")

    rows = read_orders(orders_file)
    assert rows[0]["status"] == "delivered"
    assert rows[0]["delivered_at"]


def test_estimate_order_metrics_calculates_cost_and_profit():
    metrics = estimate_order_metrics(
        price_cny=19.9,
        transcript_chars=3000,
        prompt_chars=7000,
        output_chars=5000,
        usd_to_cny=7.2,
        cost_per_1k_chars_usd=0.002,
    )

    assert metrics["estimated_cost_usd"] == "0.0300"
    assert metrics["estimated_cost_cny"] == "0.22"
    assert metrics["estimated_profit_cny"] == "19.68"
