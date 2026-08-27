from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Evidence:
    source: str
    claim: str
    facts: dict[str, Any]
    record_ids: tuple[str, ...] = ()
    calculation: str | None = None

@dataclass
class Insight:
    title: str
    level: str
    confidence: float
    summary: str
    evidence: list[Evidence] = field(default_factory=list)
    recommendation: str | None = None
