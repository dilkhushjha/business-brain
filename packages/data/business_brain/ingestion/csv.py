from __future__ import annotations

import csv
from pathlib import Path

import polars as pl

from .base import DataSourceAdapter


_HEADER_HINTS = {
    "date",
    "voucher no",
    "voucher number",
    "party name",
    "stock item",
    "quantity",
    "qty",
    "rate",
    "amount",
}


def _clean(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def _detect_header_row(path: Path, scan_limit: int = 30) -> int:
    """Return the zero-based row containing the actual tabular header.

    Tally CSV exports can contain a report title before the column header. For
    ordinary CSVs the first row remains the header.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        best_row = 0
        best_score = 0
        for row_index, row in enumerate(reader):
            if row_index >= scan_limit:
                break
            values = {_clean(value) for value in row if _clean(value)}
            score = len(values & _HEADER_HINTS)
            if score > best_score:
                best_score = score
                best_row = row_index

    return best_row if best_score >= 2 else 0


class CSVAdapter(DataSourceAdapter):
    def inspect(self, path: Path) -> dict:
        frame = self._read(path)
        return {"rows": frame.height, "columns": frame.columns}

    def ingest(self, path: Path) -> list[dict]:
        return self._read(path).to_dicts()

    @staticmethod
    def _read(path: Path) -> pl.DataFrame:
        header_row = _detect_header_row(path)
        return pl.read_csv(path, skip_rows=header_row)
