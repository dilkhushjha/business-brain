from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    normalized_name: str
    sample_values: list[Any]
    null_ratio: float


@dataclass(frozen=True)
class TableProfile:
    columns: list[ColumnProfile]
    row_count: int


def _normalize(name: str) -> str:
    return "_".join("".join(char.lower() if char.isalnum() else " " for char in name).split())


def profile_rows(rows: list[dict[str, Any]]) -> TableProfile:
    if not rows:
        return TableProfile([], 0)
    names = list(rows[0].keys())
    columns = []
    for name in names:
        values = [row.get(name) for row in rows]
        non_null = [value for value in values if value not in (None, "")]
        columns.append(
            ColumnProfile(
                name=str(name),
                normalized_name=_normalize(str(name)),
                sample_values=non_null[:5],
                null_ratio=(len(values) - len(non_null)) / len(values),
            )
        )
    return TableProfile(columns, len(rows))
