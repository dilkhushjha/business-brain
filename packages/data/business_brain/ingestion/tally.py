from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from pathlib import Path
from typing import Any

from .base import DataSourceAdapter

TOTAL_MARKERS = {"total", "grand total", "subtotal", "sub total", "net total", "closing balance"}


def clean_tally_text(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_indian_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    text = str(value).strip().replace("₹", "").replace("Rs.", "").replace("Rs", "")
    text = text.replace("INR", "").replace(",", "").strip()
    text = re.sub(r"\s*(dr|cr)\.?$", "", text, flags=re.I).strip()
    if text in {"", "-", "—"}:
        return None
    try:
        return float(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


def is_report_row(row: dict[str, Any]) -> bool:
    values = [clean_tally_text(v) for v in row.values()]
    non_empty = [v.lower() for v in values if isinstance(v, str) and v]
    if not non_empty:
        return True
    joined = " ".join(non_empty)
    return any(joined == marker or joined.startswith(marker + " ") for marker in TOTAL_MARKERS)


def normalize_tally_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        value = clean_tally_text(value)
        key_lower = str(key).strip().lower()
        if any(token in key_lower for token in ("amount", "value", "rate", "qty", "quantity", "tax")):
            parsed = parse_indian_number(value)
            normalized[key] = parsed if parsed is not None else value
        else:
            normalized[key] = value
    return normalized


def normalize_tally_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_tally_row(row) for row in rows if not is_report_row(row)]


class TallyExportAdapter(DataSourceAdapter):
    """Tally-aware cleanup shared by CSV/XLSX exports."""

    def inspect(self, path: Path) -> dict:
        rows = self.ingest(path)
        return {"path": str(path), "rows": len(rows), "status": "ready"}

    def ingest(self, path: Path) -> list[dict]:
        raise NotImplementedError("Use normalize_tally_rows with a CSV/XLSX adapter")
