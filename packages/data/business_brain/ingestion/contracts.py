from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class SourceFile:
    path: Path
    source_type: str
    checksum: str

@dataclass
class IngestionResult:
    source: SourceFile
    rows: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors
