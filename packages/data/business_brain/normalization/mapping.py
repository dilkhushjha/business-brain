from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnMapping:
    source_column: str
    canonical_field: str
    confidence: float


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(str(value).strip().lower().split())
    return value or None
