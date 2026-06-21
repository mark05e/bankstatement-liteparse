"""Base protocol for bank-specific statement extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from common.types import StatementMeta, Transaction


class BankExtractor(ABC):
    id: str
    name: str

    @abstractmethod
    def detect(self, pages: list[dict[str, Any]]) -> bool:
        """Return True if this extractor can handle the given liteparse pages."""

    @abstractmethod
    def extract_meta(self, pages: list[dict[str, Any]]) -> StatementMeta:
        """Extract statement metadata from liteparse pages."""

    @abstractmethod
    def extract_transactions(
        self,
        pages: list[dict[str, Any]],
        meta: StatementMeta | None = None,
    ) -> list[Transaction]:
        """Extract transactions from liteparse pages."""
