"""Shared data types for bank statement extraction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Transaction:
    transaction_date: str
    posting_date: str
    description: str
    amount: float
    page: int


@dataclass
class PendingTransaction:
    transaction: Transaction
    anchor_y: float


@dataclass
class StatementMeta:
    account_number: str | None = None
    statement_date: str | None = None
    statement_period_start: str | None = None
    statement_period_end: str | None = None
