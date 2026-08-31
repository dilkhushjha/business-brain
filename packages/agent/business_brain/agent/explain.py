from __future__ import annotations

from typing import Any


def evidence_summary(evidence: list[dict[str, Any]]) -> list[str]:
    out = []
    for item in evidence[:6]:
        metric = item.get("metric") or item.get("name")
        value = item.get("value")
        if metric is not None and value is not None:
            out.append(f"{metric}: {value}")
    return out


def confidence_label(confidence: float | str | None) -> str:
    """Return a display label for numeric or semantic confidence values.

    AgentResponse currently stores confidence as a string and the service uses
    the semantic value ``grounded``. Older callers may still provide a numeric
    confidence, including a numeric value serialized as a string.
    """
    if confidence is None:
        return "unknown"

    if isinstance(confidence, str):
        normalized = confidence.strip().lower()
        if normalized in {"grounded", "verified", "confirmed"}:
            return "grounded"
        try:
            confidence = float(normalized.rstrip("%"))
            if normalized.endswith("%"):
                confidence /= 100
        except ValueError:
            return "unknown"

    if confidence >= 0.8:
        return "high"
    if confidence >= 0.6:
        return "medium"
    return "low"
