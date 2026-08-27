from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SourceFile:
    name: str
    checksum: str
    size_bytes: int
    imported_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IngestionIssue:
    severity: str
    code: str
    message: str
    row_number: int | None = None
    field: str | None = None


@dataclass(frozen=True)
class IngestionResult:
    source: SourceFile
    rows_read: int
    rows_accepted: int
    rows_rejected: int
    issues: list[IngestionIssue]
