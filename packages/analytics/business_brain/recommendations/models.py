from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Recommendation:
    code: str
    title: str
    priority: str
    confidence: Decimal
    rationale: str
    evidence: dict[str, Any]
    actions: list[str]


@dataclass(frozen=True)
class RecommendationContext:
    signals: list[Any]
    drivers: list[Any]
