"""Output formatting shared across bank extractors."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from common.types import StatementMeta, Transaction


def build_output(
    transactions: list[Transaction],
    meta: StatementMeta,
    source: str,
    *,
    bank_id: str | None = None,
    bank_name: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
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
    if bank_id is not None:
        payload["bank_id"] = bank_id
    if bank_name is not None:
        payload["bank_name"] = bank_name
    return payload


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
