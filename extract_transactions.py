#!/usr/bin/env python3
"""Extract TD credit card transactions from bank statement PDFs via liteparse."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from liteparse import LiteParse

MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
FULL_MONTHS = (
    "JANUARY",
    "FEBRUARY",
    "MARCH",
    "APRIL",
    "MAY",
    "JUNE",
    "JULY",
    "AUGUST",
    "SEPTEMBER",
    "OCTOBER",
    "NOVEMBER",
    "DECEMBER",
)
DATE_RE = re.compile(rf"^({'|'.join(MONTHS)})\s+(\d{{1,2}})$", re.IGNORECASE)
AMOUNT_RE = re.compile(r"^-?\$[\d,]+\.\d{2}$")
SKIP_DESCRIPTIONS = {
    "PREVIOUS STATEMENT BALANCE",
    "TOTAL NEW BALANCE",
    "Continued",
}
STATEMENT_DATE_RE = re.compile(
    r"STATEMENT\s+DATE:\s+(\w+)\s+(\d{1,2}),\s+(\d{4})",
    re.IGNORECASE,
)
STATEMENT_PERIOD_RE = re.compile(
    r"STATEMENT\s+PERIOD:\s+(\w+)\s+(\d{1,2}),\s+(\d{4})\s+to\s+(\w+)\s+(\d{1,2}),\s+(\d{4})",
    re.IGNORECASE,
)
ACCOUNT_RE = re.compile(r"(\d{4}\s+\d{2}XX\s+XXXX\s+\d{4})")

# liteparse text_items column bands for TD transaction table (left side of page)
COL_TXN_DATE = (40, 85)
COL_POST_DATE = (85, 130)
COL_DESCRIPTION = (130, 300)
COL_AMOUNT = (300, 360)
LEFT_PANEL_MAX_X = 360
ROW_CLUSTER_TOLERANCE = 6.0
MAX_DESCRIPTION_GAP = 35.0


@dataclass
class Transaction:
    transaction_date: str
    posting_date: str
    description: str
    amount: float
    page: int


@dataclass
class _PendingTransaction:
    transaction: Transaction
    anchor_y: float


@dataclass
class StatementMeta:
    account_number: str | None = None
    statement_date: str | None = None
    statement_period_start: str | None = None
    statement_period_end: str | None = None


def _month_to_number(month_name: str) -> int:
    upper = month_name.upper()
    if upper in MONTHS:
        return MONTHS.index(upper) + 1
    if upper in FULL_MONTHS:
        return FULL_MONTHS.index(upper) + 1
    raise ValueError(f"Unknown month: {month_name}")


def _month_day_to_iso(month_name: str, day: str, year: int) -> str:
    month = _month_to_number(month_name)
    return f"{year:04d}-{month:02d}-{int(day):02d}"


def _parse_amount(text: str) -> float:
    return float(text.replace("$", "").replace(",", ""))


def _column_for_x(x: float) -> str | None:
    if COL_TXN_DATE[0] <= x < COL_TXN_DATE[1]:
        return "txn_date"
    if COL_POST_DATE[0] <= x < COL_POST_DATE[1]:
        return "post_date"
    if COL_DESCRIPTION[0] <= x < COL_DESCRIPTION[1]:
        return "description"
    if COL_AMOUNT[0] <= x < COL_AMOUNT[1]:
        return "amount"
    return None


def _cluster_rows(items: list[dict[str, Any]], tolerance: float = ROW_CLUSTER_TOLERANCE) -> list[dict[str, Any]]:
    sorted_items = sorted(items, key=lambda item: item["y"])
    clusters: list[dict[str, Any]] = []
    for item in sorted_items:
        for cluster in clusters:
            if abs(item["y"] - cluster["y_ref"]) <= tolerance:
                cluster["items"].append(item)
                break
        else:
            clusters.append({"y_ref": item["y"], "items": [item]})
    return clusters


def _extract_meta(pages: list[dict[str, Any]]) -> StatementMeta:
    meta = StatementMeta()
    for page in pages:
        text = page.get("text", "")
        if not meta.statement_date:
            match = STATEMENT_DATE_RE.search(text)
            if match:
                meta.statement_date = _month_day_to_iso(match.group(1), match.group(2), int(match.group(3)))
        if not meta.statement_period_start:
            match = STATEMENT_PERIOD_RE.search(text)
            if match:
                start_year = int(match.group(3))
                end_year = int(match.group(6))
                meta.statement_period_start = _month_day_to_iso(match.group(1), match.group(2), start_year)
                meta.statement_period_end = _month_day_to_iso(match.group(4), match.group(5), end_year)
        if not meta.account_number:
            match = ACCOUNT_RE.search(text)
            if match:
                meta.account_number = match.group(1)
        if meta.statement_date and meta.statement_period_start and meta.account_number:
            break
    return meta


def _infer_year(txn_month: str, meta: StatementMeta) -> int:
    if meta.statement_date:
        return int(meta.statement_date[:4])
    if meta.statement_period_end:
        return int(meta.statement_period_end[:4])
    return 2024


def _year_for_month_number(month_num: int, meta: StatementMeta) -> int:
    if meta.statement_period_start and meta.statement_period_end:
        start_y = int(meta.statement_period_start[:4])
        start_m = int(meta.statement_period_start[5:7])
        end_y = int(meta.statement_period_end[:4])
        end_m = int(meta.statement_period_end[5:7])
        if start_y == end_y:
            return start_y
        if month_num >= start_m:
            return start_y
        return end_y
    return _infer_year("", meta)


def _normalize_date(raw: str, meta: StatementMeta) -> str:
    match = DATE_RE.match(raw.strip())
    if not match:
        return raw.strip()
    month_num = _month_to_number(match.group(1))
    day = match.group(2)
    year = _year_for_month_number(month_num, meta)
    return f"{year:04d}-{month_num:02d}-{int(day):02d}"


def _row_fields(cluster: dict[str, Any]) -> dict[str, str | None]:
    fields: dict[str, str | None] = {
        "txn_date": None,
        "post_date": None,
        "description": None,
        "amount": None,
    }
    descriptions: list[str] = []
    for item in sorted(cluster["items"], key=lambda entry: entry["x"]):
        column = _column_for_x(item["x"])
        text = item["text"].strip()
        if not text or column is None:
            continue
        if column == "description":
            descriptions.append(text)
        else:
            fields[column] = text
    if descriptions:
        fields["description"] = " ".join(descriptions)
    return fields


def extract_transactions_from_pages(pages: list[dict[str, Any]], meta: StatementMeta | None = None) -> list[Transaction]:
    meta = meta or _extract_meta(pages)
    transactions: list[Transaction] = []
    pending: _PendingTransaction | None = None

    def flush_pending() -> None:
        nonlocal pending
        if pending:
            transactions.append(pending.transaction)
            pending = None

    for page in pages:
        page_num = page["page"]
        if "TRANSACTION POSTING" not in page.get("text", ""):
            continue

        left_items = [item for item in page.get("text_items", []) if item["x"] < LEFT_PANEL_MAX_X]
        for cluster in sorted(_cluster_rows(left_items), key=lambda entry: entry["y_ref"]):
            fields = _row_fields(cluster)
            txn_raw = fields["txn_date"]
            post_raw = fields["post_date"]
            description = fields["description"]
            amount_raw = fields["amount"]

            if txn_raw and DATE_RE.match(txn_raw) and amount_raw and AMOUNT_RE.match(amount_raw):
                desc = description or ""
                if desc.upper() in SKIP_DESCRIPTIONS:
                    flush_pending()
                    continue

                flush_pending()
                pending = _PendingTransaction(
                    transaction=Transaction(
                        transaction_date=_normalize_date(txn_raw, meta),
                        posting_date=_normalize_date(post_raw or txn_raw, meta),
                        description=desc,
                        amount=_parse_amount(amount_raw),
                        page=page_num,
                    ),
                    anchor_y=cluster["y_ref"],
                )
                continue

            if (
                pending
                and pending.transaction.page == page_num
                and description
                and not txn_raw
                and not amount_raw
                and cluster["y_ref"] - pending.anchor_y <= MAX_DESCRIPTION_GAP
            ):
                pending.transaction.description = f"{pending.transaction.description} {description}".strip()
                pending.anchor_y = cluster["y_ref"]

    flush_pending()
    return transactions


def parse_pdf(pdf_path: Path, *, quiet: bool = True) -> tuple[list[dict[str, Any]], StatementMeta]:
    parser = LiteParse(output_format="json", quiet=quiet)
    result = parser.parse(pdf_path)
    pages = [
        {
            "page": page.page_num,
            "width": page.width,
            "height": page.height,
            "text": page.text,
            "text_items": [
                {
                    "text": item.text,
                    "x": item.x,
                    "y": item.y,
                    "width": item.width,
                    "height": item.height,
                }
                for item in page.text_items
            ],
        }
        for page in result.pages
    ]
    meta = _extract_meta(pages)
    return pages, meta


def load_liteparse_json(json_path: Path) -> tuple[list[dict[str, Any]], StatementMeta]:
    with json_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    pages = data["pages"]
    return pages, _extract_meta(pages)


def build_output(
    transactions: list[Transaction],
    meta: StatementMeta,
    source: str,
) -> dict[str, Any]:
    return {
        "source": source,
        "account_number": meta.account_number,
        "statement_date": meta.statement_date,
        "statement_period": {
            "start": meta.statement_period_start,
            "end": meta.statement_period_end,
        },
        "transaction_count": len(transactions),
        "transactions": [asdict(txn) for txn in transactions],
    }


def write_csv(transactions: list[Transaction], path: Path) -> None:
    fieldnames = ["transaction_date", "posting_date", "description", "amount", "page"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for txn in transactions:
            writer.writerow(asdict(txn))


def write_json(payload: dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract TD credit card transactions from statement PDFs.")
    parser.add_argument("input", type=Path, help="PDF path or existing liteparse JSON output")
    parser.add_argument("--csv", type=Path, help="Write transactions CSV to this path")
    parser.add_argument("--json", type=Path, help="Write structured JSON to this path")
    parser.add_argument("--verbose", action="store_true", help="Show liteparse progress output")
    args = parser.parse_args(argv)

    input_path = args.input
    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 1

    if input_path.suffix.lower() == ".json":
        pages, meta = load_liteparse_json(input_path)
        source = str(input_path)
    else:
        pages, meta = parse_pdf(input_path, quiet=not args.verbose)
        source = str(input_path)

    transactions = extract_transactions_from_pages(pages, meta)
    payload = build_output(transactions, meta, source)

    json_path = args.json or input_path.with_suffix(".transactions.json")
    csv_path = args.csv or input_path.with_suffix(".transactions.csv")

    write_json(payload, json_path)
    write_csv(transactions, csv_path)

    print(f"Extracted {len(transactions)} transactions")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
