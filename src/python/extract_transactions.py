#!/usr/bin/env python3
"""Extract credit card transactions from bank statement PDFs via liteparse."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow imports from src/python/ when run as a script.
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from banks.registry import detect_extractor, get_extractor, list_extractors
from common.output import build_output, write_csv, write_json
from common.pdf import load_liteparse_json, parse_pdf


def main(argv: list[str] | None = None) -> int:
    bank_ids = [extractor.id for extractor in list_extractors()]
    parser = argparse.ArgumentParser(
        description="Extract credit card transactions from statement PDFs.",
    )
    parser.add_argument("input", type=Path, help="PDF path or existing liteparse JSON output")
    parser.add_argument(
        "--bank",
        choices=bank_ids,
        help="Bank extractor to use (default: auto-detect from statement content)",
    )
    parser.add_argument("--csv", type=Path, help="Write transactions CSV to this path")
    parser.add_argument("--json", type=Path, help="Write structured JSON to this path")
    parser.add_argument("--verbose", action="store_true", help="Show liteparse progress output")
    args = parser.parse_args(argv)

    input_path = args.input
    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 1

    if input_path.suffix.lower() == ".json":
        pages = load_liteparse_json(input_path)
        source = str(input_path)
    else:
        pages = parse_pdf(input_path, quiet=not args.verbose)
        source = str(input_path)

    if args.bank:
        extractor = get_extractor(args.bank)
    else:
        extractor = detect_extractor(pages)
        if extractor is None:
            known = ", ".join(bank_ids)
            print(
                f"Could not detect bank from statement. Try --bank explicitly. Known banks: {known}",
                file=sys.stderr,
            )
            return 1

    meta = extractor.extract_meta(pages)
    transactions = extractor.extract_transactions(pages, meta)
    payload = build_output(
        transactions,
        meta,
        source,
        bank_id=extractor.id,
        bank_name=extractor.name,
    )

    json_path = args.json or input_path.with_suffix(".transactions.json")
    csv_path = args.csv or input_path.with_suffix(".transactions.csv")

    write_json(payload, json_path)
    write_csv(transactions, csv_path)

    print(f"Bank: {extractor.name} ({extractor.id})")
    print(f"Extracted {len(transactions)} transactions")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
