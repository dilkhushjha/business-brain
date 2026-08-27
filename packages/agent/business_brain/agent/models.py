from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentRequest:
    question: str
    business_id: str
    as_of: str | None = None


@dataclass(frozen=True)
class AgentResponse:
    answer: str
    intent: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    signals: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    confidence: str = "unknown"
