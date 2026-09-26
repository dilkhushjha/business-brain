from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BusinessRisk:
    code: str
    title: str
    level: str
    score: Decimal
    confidence: Decimal
    signal_codes: list[str]
    evidence: dict[str, Any]
    explanation: str
    recommended_next_step: str


_RISK_RULES = {
    "CASH_FLOW_RISK": {
        "title": "Cash flow risk",
        "signals": {"RECEIVABLE_OVERDUE", "PAYABLE_OVERDUE"},
        "base": Decimal("45"),
        "step": "Review overdue collections and supplier payment timing before committing to new cash outflows.",
    },
    "MARGIN_RISK": {
        "title": "Margin risk",
        "signals": {"PRODUCT_MARGIN_DETERIORATION", "SUPPLIER_PRICE_INCREASE", "EXPENSE_SPIKE"},
        "base": Decimal("40"),
        "step": "Review the affected costs and selling prices before margin pressure becomes persistent.",
    },
    "INVENTORY_RISK": {
        "title": "Inventory risk",
        "signals": {"STOCKOUT_RISK", "EXCESS_INVENTORY", "NEGATIVE_INVENTORY", "PRODUCT_SLOW_MOVING"},
        "base": Decimal("40"),
        "step": "Reconcile stock first, then review replenishment and slow-moving inventory decisions.",
    },
    "CUSTOMER_RISK": {
        "title": "Customer risk",
        "signals": {"CUSTOMER_REVENUE_DECLINE", "CUSTOMER_INACTIVE"},
        "base": Decimal("35"),
        "step": "Review affected customers and investigate whether the change is temporary or persistent.",
    },
    "SUPPLIER_RISK": {
        "title": "Supplier risk",
        "signals": {"SUPPLIER_PRICE_INCREASE", "SUPPLIER_CONCENTRATION", "SUPPLIER_SPEND_SPIKE"},
        "base": Decimal("35"),
        "step": "Review supplier dependency, pricing changes and viable alternatives.",
    },
    "DATA_INTEGRITY_RISK": {
        "title": "Data integrity risk",
        "signals": {"NEGATIVE_INVENTORY"},
        "base": Decimal("60"),
        "step": "Reconcile the underlying source data before relying on affected operational conclusions.",
    },
}


def _level(score: Decimal) -> str:
    if score >= Decimal("75"):
        return "critical"
    if score >= Decimal("55"):
        return "high"
    if score >= Decimal("35"):
        return "medium"
    return "low"


def detect_business_risks(
    signals: list[Any],
    integrity: dict[str, Any] | None = None,
) -> list[BusinessRisk]:
    """Aggregate independent signals into explainable business-risk assessments.

    Risk is a current exposure indicator, not a forecast. Scores are a
    deterministic heuristic based only on detected signal severity/confidence.
    Missing evidence never creates a risk.
    """
    integrity = integrity or {}
    by_code: dict[str, list[Any]] = {}
    for signal in signals:
        by_code.setdefault(str(getattr(signal, "code", "")), []).append(signal)

    risks: list[BusinessRisk] = []
    for code, rule in _RISK_RULES.items():
        matched_codes = [s for s in rule["signals"] if s in by_code]
        if not matched_codes:
            continue

        matched = [item for signal_code in matched_codes for item in by_code[signal_code]]
        max_severity = max(
            (str(getattr(item, "severity", "info")).lower() for item in matched),
            key=lambda value: {"critical": 4, "high": 3, "warning": 2, "medium": 2, "info": 1, "positive": 0}.get(value, 0),
        )
        severity_weight = {
            "critical": Decimal("30"),
            "high": Decimal("25"),
            "warning": Decimal("18"),
            "medium": Decimal("15"),
            "info": Decimal("5"),
            "positive": Decimal("0"),
        }.get(max_severity, Decimal("5"))
        confidence = max(
            (Decimal(str(getattr(item, "confidence", "0"))) for item in matched),
            default=Decimal("0"),
        )
        score = min(
            Decimal("100"),
            rule["base"] + severity_weight + (confidence * Decimal("25")) + Decimal(max(0, len(matched_codes) - 1) * 5),
        )

        evidence: dict[str, Any] = {
            "signal_codes": matched_codes,
            "signals": [
                {
                    "code": str(getattr(item, "code", "")),
                    "title": str(getattr(item, "title", "")),
                    "severity": str(getattr(item, "severity", "")),
                    "confidence": str(getattr(item, "confidence", "")),
                    "evidence": dict(getattr(item, "evidence", {}) or {}),
                }
                for item in matched
            ],
        }

        if integrity.get("status") == "attention_required":
            evidence["integrity_status"] = "attention_required"
            evidence["integrity_domains"] = list(integrity.get("affected_domains") or [])
            affected = set(integrity.get("affected_domains") or [])
            relevant = {"data_quality", "inventory"} if code in {"INVENTORY_RISK", "MARGIN_RISK", "SUPPLIER_RISK"} else affected
            if relevant & affected:
                confidence = min(confidence, Decimal("0.65"))
                score = min(score, Decimal("69"))

        risks.append(
            BusinessRisk(
                code=code,
                title=rule["title"],
                level=_level(score),
                score=score,
                confidence=confidence,
                signal_codes=matched_codes,
                evidence=evidence,
                explanation=(
                    f"{len(matched)} detected signal(s) indicate current {rule['title'].lower()} exposure. "
                    "This is an evidence-based risk indicator, not a prediction of a future outcome."
                ),
                recommended_next_step=rule["step"],
            )
        )

    return sorted(risks, key=lambda risk: (-risk.score, risk.code))
