"""TD Bank credit card statement extractor."""

from __future__ import annotations

import re
from typing import Any

from banks.base import BankExtractor
from common.clustering import cluster_rows, parse_amount, row_fields
from common.dates import MONTH_DAY_DATE_RE, month_day_to_iso, normalize_month_day_date
from common.types import PendingTransaction, StatementMeta, Transaction

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
AMOUNT_RE = re.compile(r"^-?\$[\d,]+\.\d{2}$")

# liteparse text_items column bands for TD transaction table (left side of page)
COLUMNS = {
    "txn_date": (40, 85),
    "post_date": (85, 130),
    "description": (130, 300),
    "amount": (300, 360),
}
LEFT_PANEL_MAX_X = 360
ROW_CLUSTER_TOLERANCE = 6.0
MAX_DESCRIPTION_GAP = 35.0
TRANSACTION_PAGE_MARKER = "TRANSACTION POSTING"


class TdCreditExtractor(BankExtractor):
    id = "td_credit"
    name = "TD Credit Card"

    def detect(self, pages: list[dict[str, Any]]) -> bool:
        for page in pages:
            text = page.get("text", "")
            if TRANSACTION_PAGE_MARKER in text and ACCOUNT_RE.search(text):
                return True
        return False

    def extract_meta(self, pages: list[dict[str, Any]]) -> StatementMeta:
        meta = StatementMeta()
        for page in pages:
            text = page.get("text", "")
            if not meta.statement_date:
                match = STATEMENT_DATE_RE.search(text)
                if match:
                    meta.statement_date = month_day_to_iso(match.group(1), match.group(2), int(match.group(3)))
            if not meta.statement_period_start:
                match = STATEMENT_PERIOD_RE.search(text)
                if match:
                    start_year = int(match.group(3))
                    end_year = int(match.group(6))
                    meta.statement_period_start = month_day_to_iso(match.group(1), match.group(2), start_year)
                    meta.statement_period_end = month_day_to_iso(match.group(4), match.group(5), end_year)
            if not meta.account_number:
                match = ACCOUNT_RE.search(text)
                if match:
                    meta.account_number = match.group(1)
            if meta.statement_date and meta.statement_period_start and meta.account_number:
                break
        return meta

    def extract_transactions(
        self,
        pages: list[dict[str, Any]],
        meta: StatementMeta | None = None,
    ) -> list[Transaction]:
        meta = meta or self.extract_meta(pages)
        transactions: list[Transaction] = []
        pending: PendingTransaction | None = None

        def flush_pending() -> None:
            nonlocal pending
            if pending:
                transactions.append(pending.transaction)
                pending = None

        for page in pages:
            page_num = page["page"]
            if TRANSACTION_PAGE_MARKER not in page.get("text", ""):
                continue

            left_items = [item for item in page.get("text_items", []) if item["x"] < LEFT_PANEL_MAX_X]
            for cluster in sorted(
                cluster_rows(left_items, tolerance=ROW_CLUSTER_TOLERANCE),
                key=lambda entry: entry["y_ref"],
            ):
                fields = row_fields(cluster, COLUMNS)
                txn_raw = fields["txn_date"]
                post_raw = fields["post_date"]
                description = fields["description"]
                amount_raw = fields["amount"]

                if (
                    txn_raw
                    and MONTH_DAY_DATE_RE.match(txn_raw)
                    and amount_raw
                    and AMOUNT_RE.match(amount_raw)
                ):
                    desc = description or ""
                    if desc.upper() in SKIP_DESCRIPTIONS:
                        flush_pending()
                        continue

                    flush_pending()
                    pending = PendingTransaction(
                        transaction=Transaction(
                            transaction_date=normalize_month_day_date(txn_raw, meta),
                            posting_date=normalize_month_day_date(post_raw or txn_raw, meta),
                            description=desc,
                            amount=parse_amount(amount_raw),
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
