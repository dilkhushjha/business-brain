from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Signal:
    code: str
    title: str
    severity: str
    confidence: Decimal
    metric: str
    current_value: Decimal | None
    baseline_value: Decimal | None
    change: Decimal | None
    evidence: dict[str, Any]
    recommended_next_step: str
