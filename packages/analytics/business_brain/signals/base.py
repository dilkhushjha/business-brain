from dataclasses import dataclass
from typing import Any
from packages.domain.business_brain.enums.severity import Severity
@dataclass(frozen=True)
class Signal:
    type: str
    severity: Severity
    confidence: float
    entity_id: str | None
    evidence: list[dict[str, Any]]
    financial_impact: float | None = None
