from pathlib import Path
from typing import Any

import polars as pl


def inspect_csv(path: Path) -> dict[str, Any]:
    frame = pl.read_csv(path, infer_schema_length=1000)
    return {
        "format": "csv",
        "rows": frame.height,
        "columns": frame.columns,
        "dtypes": {name: str(dtype) for name, dtype in zip(frame.columns, frame.dtypes)},
        "null_counts": frame.null_count().to_dicts()[0],
    }


def inspect_excel(path: Path) -> dict[str, Any]:
    frame = pl.read_excel(path)
    return {
        "format": "excel",
        "rows": frame.height,
        "columns": frame.columns,
        "dtypes": {name: str(dtype) for name, dtype in zip(frame.columns, frame.dtypes)},
        "null_counts": frame.null_count().to_dicts()[0],
    }
