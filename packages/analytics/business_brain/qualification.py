from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Any


# Integrity domains that can materially weaken conclusions based on the
# corresponding business situation. Data-quality issues are intentionally broad:
# ambiguous identities or broken documents can affect cross-domain reasoning.
_SITUATION_DOMAINS = {
    "MARGIN_PRESSURE": {"data_quality", "inventory"},
    "SUPPLIER_DEPENDENCY_PRESSURE": {"data_quality", "inventory"},
    "PROCUREMENT_DEMAND_PRESSURE": {"data_quality", "inventory"},
    "WORKING_CAPITAL_PRESSURE": {"data_quality", "financial"},
    "PROFITABILITY_PRESSURE": {"data_quality", "financial", "inventory"},
    "REVENUE_COST_SQUEEZE": {"data_quality", "financial"},
}

# A qualified conclusion remains useful, but cannot retain the same confidence
# as a conclusion built from reconciled data.
_QUALIFIED_CONFIDENCE_CAP = Decimal("0.65")


def _quality_confidence_cap(integrity: dict[str, Any], relevant: set[str]) -> Decimal:
    issue_count = sum(
        int((integrity.get("audits", {}).get(domain, {}).get("summary", {}) or {}).get("issue_count", 0))
        for domain in relevant
    )
    if issue_count >= 5:
        return Decimal("0.40")
    if issue_count >= 2:
        return Decimal("0.50")
    return _QUALIFIED_CONFIDENCE_CAP


def qualify_situations(
    situations: list[Any],
    integrity: dict[str, Any] | None,
) -> list[Any]:
    """Attach integrity caveats to situations when source data has exceptions.

    This does not delete a situation or invent a new one. It makes uncertainty
    explicit when an unresolved integrity domain can affect the conclusion.
    """
    integrity = integrity or {}
    affected_domains = set(integrity.get("affected_domains") or [])
    if not affected_domains:
        return situations

    qualified: list[Any] = []
    for situation in situations:
        code = str(getattr(situation, "code", ""))
        relevant = _SITUATION_DOMAINS.get(code, {"data_quality"}) & affected_domains
        if not relevant:
            qualified.append(situation)
            continue

        evidence = dict(getattr(situation, "evidence", {}) or {})
        evidence["integrity_status"] = "attention_required"
        evidence["integrity_domains"] = sorted(relevant)

        confidence = Decimal(str(getattr(situation, "confidence", "0")))
        confidence = min(confidence, _quality_confidence_cap(integrity, relevant))

        explanation = str(getattr(situation, "explanation", ""))
        caveat = (
            " Conclusion is qualified because unresolved "
            + ", ".join(sorted(relevant))
            + " integrity issues may affect the supporting data."
        )

        qualified.append(
            replace(
                situation,
                confidence=confidence,
                evidence=evidence,
                explanation=explanation + caveat,
            )
        )

    return qualified
