"""Spatial clustering helpers for liteparse text items."""

from __future__ import annotations

from typing import Any

DEFAULT_ROW_CLUSTER_TOLERANCE = 6.0


def parse_amount(text: str) -> float:
    return float(text.replace("$", "").replace(",", ""))


def column_for_x(x: float, columns: dict[str, tuple[float, float]]) -> str | None:
    for name, (low, high) in columns.items():
        if low <= x < high:
            return name
    return None


def cluster_rows(
    items: list[dict[str, Any]],
    tolerance: float = DEFAULT_ROW_CLUSTER_TOLERANCE,
) -> list[dict[str, Any]]:
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


def row_fields(
    cluster: dict[str, Any],
    columns: dict[str, tuple[float, float]],
    *,
    merge_column: str = "description",
) -> dict[str, str | None]:
    fields: dict[str, str | None] = {name: None for name in columns}
    merged: list[str] = []
    for item in sorted(cluster["items"], key=lambda entry: entry["x"]):
        column = column_for_x(item["x"], columns)
        text = item["text"].strip()
        if not text or column is None:
            continue
        if column == merge_column:
            merged.append(text)
        else:
            fields[column] = text
    if merged:
        fields[merge_column] = " ".join(merged)
    return fields
