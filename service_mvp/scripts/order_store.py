from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ORDER_FIELDS = [
    "order_id",
    "customer_name",
    "customer_contact",
    "youtube_url",
    "case_id",
    "case_title",
    "price_cny",
    "status",
    "created_at",
    "delivered_at",
    "transcript_chars",
    "prompt_chars",
    "output_chars",
    "estimated_cost_usd",
    "estimated_cost_cny",
    "estimated_profit_cny",
    "case_dir",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def order_id_from_case_id(case_id: str) -> str:
    value = case_id.strip()
    if value.startswith("case_"):
        value = value.removeprefix("case_")
    if value.startswith("ord_"):
        return value
    return f"ord_{value or 'manual'}"


def estimate_order_metrics(
    *,
    price_cny: float,
    transcript_chars: int = 0,
    prompt_chars: int = 0,
    output_chars: int = 0,
    usd_to_cny: float = 7.2,
    cost_per_1k_chars_usd: float = 0.002,
) -> dict[str, str]:
    total_chars = max(0, transcript_chars) + max(0, prompt_chars) + max(0, output_chars)
    estimated_cost_usd = (total_chars / 1000) * cost_per_1k_chars_usd
    estimated_cost_cny = estimated_cost_usd * usd_to_cny
    estimated_profit_cny = price_cny - estimated_cost_cny
    return {
        "estimated_cost_usd": f"{estimated_cost_usd:.4f}",
        "estimated_cost_cny": f"{estimated_cost_cny:.2f}",
        "estimated_profit_cny": f"{estimated_profit_cny:.2f}",
    }


def read_orders(orders_file: Path) -> list[dict[str, str]]:
    if not orders_file.exists():
        return []
    with orders_file.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_orders(orders_file: Path, rows: list[dict[str, Any]]) -> None:
    orders_file.parent.mkdir(parents=True, exist_ok=True)
    with orders_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=ORDER_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in ORDER_FIELDS})


def save_order(
    *,
    orders_file: Path,
    order_id: str,
    customer_name: str,
    customer_contact: str,
    youtube_url: str,
    case_id: str,
    case_title: str,
    price_cny: float,
    status: str,
    case_dir: str,
    transcript_chars: int = 0,
    prompt_chars: int = 0,
    output_chars: int = 0,
) -> dict[str, str]:
    rows = read_orders(orders_file)
    now = utc_now_iso()
    existing = next((row for row in rows if row.get("order_id") == order_id), {})
    metrics = estimate_order_metrics(
        price_cny=price_cny,
        transcript_chars=transcript_chars,
        prompt_chars=prompt_chars,
        output_chars=output_chars,
    )
    delivered_at = existing.get("delivered_at", "")
    if status == "delivered" and not delivered_at:
        delivered_at = now
    saved = {
        "order_id": order_id,
        "customer_name": customer_name.strip(),
        "customer_contact": customer_contact.strip(),
        "youtube_url": youtube_url.strip(),
        "case_id": case_id.strip(),
        "case_title": case_title.strip(),
        "price_cny": f"{price_cny:.2f}",
        "status": status.strip() or "new",
        "created_at": existing.get("created_at") or now,
        "delivered_at": delivered_at,
        "transcript_chars": str(max(0, transcript_chars)),
        "prompt_chars": str(max(0, prompt_chars)),
        "output_chars": str(max(0, output_chars)),
        "case_dir": case_dir,
        **metrics,
    }

    upserted = False
    new_rows: list[dict[str, str]] = []
    for row in rows:
        if row.get("order_id") == order_id:
            new_rows.append(saved)
            upserted = True
        else:
            new_rows.append(row)
    if not upserted:
        new_rows.append(saved)
    write_orders(orders_file, new_rows)
    return saved


def update_order_status(orders_file: Path, order_id: str, status: str) -> dict[str, str]:
    rows = read_orders(orders_file)
    now = utc_now_iso()
    updated: dict[str, str] | None = None
    for row in rows:
        if row.get("order_id") == order_id:
            row["status"] = status
            if status == "delivered" and not row.get("delivered_at"):
                row["delivered_at"] = now
            updated = row
            break
    if updated is None:
        raise ValueError(f"Order not found: {order_id}")
    write_orders(orders_file, rows)
    return updated


def _to_float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def summarize_orders(
    orders_file: Path,
    *,
    monthly_token_budget_usd: float = 40,
    usd_to_cny: float = 7.2,
) -> dict[str, int | str]:
    rows = read_orders(orders_file)
    revenue_statuses = {"paid", "processing", "delivered"}
    revenue_rows = [row for row in rows if row.get("status") in revenue_statuses]
    revenue_cny = sum(_to_float(row.get("price_cny", "0")) for row in revenue_rows)
    estimated_profit_cny = sum(_to_float(row.get("estimated_profit_cny", "0")) for row in revenue_rows)
    token_budget_cny = monthly_token_budget_usd * usd_to_cny
    token_budget_gap_cny = max(0.0, token_budget_cny - estimated_profit_cny)
    progress_pct = 0.0 if token_budget_cny <= 0 else min(100.0, estimated_profit_cny / token_budget_cny * 100)

    return {
        "total_orders": len(rows),
        "paid_orders": sum(1 for row in rows if row.get("status") in {"paid", "processing", "delivered"}),
        "delivered_orders": sum(1 for row in rows if row.get("status") == "delivered"),
        "cancelled_orders": sum(1 for row in rows if row.get("status") == "cancelled"),
        "revenue_cny": f"{revenue_cny:.2f}",
        "estimated_profit_cny": f"{estimated_profit_cny:.2f}",
        "token_budget_cny": f"{token_budget_cny:.2f}",
        "token_budget_gap_cny": f"{token_budget_gap_cny:.2f}",
        "token_budget_progress_pct": f"{progress_pct:.2f}",
    }
