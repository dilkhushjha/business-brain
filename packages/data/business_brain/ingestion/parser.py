from __future__ import annotations
import csv
from pathlib import Path
from typing import Any, Iterator


def read_csv(path: str | Path) -> Iterator[dict[str, Any]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        for row in reader:
            yield {str(k).strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k is not None}


def read_file(path: str | Path) -> Iterator[dict[str, Any]]:
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        yield from read_csv(path)
        return
    if suffix in {".xlsx", ".xls"}:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Excel import requires pandas/openpyxl") from exc
        frame = pd.read_excel(path)
        for row in frame.where(frame.notna(), None).to_dict(orient="records"):
            yield row
        return
    raise ValueError(f"Unsupported file type: {suffix}. Use CSV or Excel.")
