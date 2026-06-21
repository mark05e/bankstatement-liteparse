"""Registry of bank statement extractors."""

from __future__ import annotations

from typing import Any

from banks.base import BankExtractor
from banks.td_credit import TdCreditExtractor

_EXTRACTORS: dict[str, BankExtractor] = {
    TdCreditExtractor.id: TdCreditExtractor(),
}


def list_extractors() -> list[BankExtractor]:
    return list(_EXTRACTORS.values())


def get_extractor(bank_id: str) -> BankExtractor:
    extractor = _EXTRACTORS.get(bank_id)
    if extractor is None:
        known = ", ".join(sorted(_EXTRACTORS))
        raise ValueError(f"Unknown bank: {bank_id!r}. Known banks: {known}")
    return extractor


def detect_extractor(pages: list[dict[str, Any]]) -> BankExtractor | None:
    for extractor in _EXTRACTORS.values():
        if extractor.detect(pages):
            return extractor
    return None
