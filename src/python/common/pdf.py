"""LiteParse PDF/JSON loading shared across bank extractors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from liteparse import LiteParse

from common.types import StatementMeta


def liteparse_result_to_pages(result: Any) -> list[dict[str, Any]]:
    return [
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


def parse_pdf(pdf_path: Path, *, quiet: bool = True) -> list[dict[str, Any]]:
    parser = LiteParse(output_format="json", quiet=quiet)
    result = parser.parse(pdf_path)
    return liteparse_result_to_pages(result)


def load_liteparse_json(json_path: Path) -> list[dict[str, Any]]:
    with json_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data["pages"]
