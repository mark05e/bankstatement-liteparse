"""Date parsing helpers shared across bank extractors."""

from __future__ import annotations

import re

from common.types import StatementMeta

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
MONTH_DAY_DATE_RE = re.compile(rf"^({'|'.join(MONTHS)})\s+(\d{{1,2}})$", re.IGNORECASE)


def month_to_number(month_name: str) -> int:
    upper = month_name.upper()
    if upper in MONTHS:
        return MONTHS.index(upper) + 1
    if upper in FULL_MONTHS:
        return FULL_MONTHS.index(upper) + 1
    raise ValueError(f"Unknown month: {month_name}")


def month_day_to_iso(month_name: str, day: str, year: int) -> str:
    month = month_to_number(month_name)
    return f"{year:04d}-{month:02d}-{int(day):02d}"


def infer_year(meta: StatementMeta) -> int:
    if meta.statement_date:
        return int(meta.statement_date[:4])
    if meta.statement_period_end:
        return int(meta.statement_period_end[:4])
    return 2024


def year_for_month_number(month_num: int, meta: StatementMeta) -> int:
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
    return infer_year(meta)


def normalize_month_day_date(raw: str, meta: StatementMeta) -> str:
    match = MONTH_DAY_DATE_RE.match(raw.strip())
    if not match:
        return raw.strip()
    month_num = month_to_number(match.group(1))
    day = match.group(2)
    year = year_for_month_number(month_num, meta)
    return f"{year:04d}-{month_num:02d}-{int(day):02d}"
