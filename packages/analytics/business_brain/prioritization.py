from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SituationPriority:
    """A deterministic attention priority derived from business evidence."""

    situation_code: str
    level: str
    score: Decimal
    reasons: list[str]


_SEVERITY_WEIGHT = {
    "critical": Decimal("40"),
    "warning": Decimal("25"),
    "high": Decimal("30"),
    "medium": Decimal("15"),
    "info": Decimal("5"),
}


def _impact_weight(analysis: Any | None) -> Decimal:
    if analysis is None:
        return Decimal("0")

    impacts = getattr(analysis, "impacts", []) or []
    if not impacts:
        return Decimal("0")

    if any(getattr(impact, "value", None) is not None for impact in impacts):
        return Decimal("10")
    return Decimal("0")


def prioritize_situations(
    situations: list[Any],
    analyses: list[Any] | None = None,
) -> list[SituationPriority]:
    """Rank situations for attention without inventing business impact.

    The score is an explainable attention heuristic, not a financial forecast.
    It uses only documented situation severity/confidence and whether the
    existing analysis contains measurable impact.
    """
    analysis_by_code = {
        getattr(item, "situation_code", ""): item
        for item in (analyses or [])
    }

    priorities: list[SituationPriority] = []
    for situation in situations:
        severity = str(getattr(situation, "severity", "info")).lower()
        confidence = Decimal(str(getattr(situation, "confidence", "0")))
        score = _SEVERITY_WEIGHT.get(severity, Decimal("0"))
        score += confidence * Decimal("30")

        analysis = analysis_by_code.get(getattr(situation, "code", ""))
        impact_weight = _impact_weight(analysis)
        score += impact_weight

        reasons = [
            f"severity={severity}",
            f"confidence={confidence:.2f}",
        ]
        if impact_weight:
            reasons.append("has measurable impact evidence")
        else:
            reasons.append("no measurable impact value available")

        priorities.append(SituationPriority(
            situation_code=situation.code,
            level="immediate" if score >= 70 else "attention" if score >= 45 else "monitor",
            score=score,
            reasons=reasons,
        ))

    return sorted(
        priorities,
        key=lambda item: (-item.score, item.situation_code),
    )
