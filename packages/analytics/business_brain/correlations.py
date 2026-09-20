from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BusinessSituation:
    """A correlated business condition built from multiple independent signals."""

    code: str
    title: str
    severity: str
    confidence: Decimal
    signal_codes: list[str]
    evidence: dict[str, Any]
    explanation: str
    recommended_next_step: str


def _unique_codes(signals: list[Any]) -> list[str]:
    """Return signal codes in stable first-seen order."""
    return list(dict.fromkeys(s.code for s in signals))


def _signal_evidence(signal: Any, key: str) -> Any:
    return (getattr(signal, "evidence", None) or {}).get(key)


def correlate_signals(signals: list[Any], state: Any | None = None) -> list[BusinessSituation]:
    """Collapse related signals into evidence-backed cross-domain situations.

    Correlation is deliberately conservative: a situation requires specific
    signal combinations and never invents a causal relationship when evidence
    is absent. The optional BusinessState enriches evidence where the canonical
    state contains a relevant metric, but it is never used to manufacture a
    situation without its required signals.
    """
    by_code: dict[str, list[Any]] = {}
    for signal in signals:
        by_code.setdefault(signal.code, []).append(signal)

    situations: list[BusinessSituation] = []

    price = by_code.get("SUPPLIER_PRICE_INCREASE", [])
    margin = by_code.get("PRODUCT_MARGIN_DETERIORATION", [])
    if price and margin:
        price_products = {
            _signal_evidence(s, "product")
            for s in price
            if _signal_evidence(s, "product")
        }
        margin_products = {
            _signal_evidence(s, "product")
            for s in margin
            if _signal_evidence(s, "product")
        }
        overlap = sorted(price_products & margin_products)
        if overlap:
            related = price + margin
            evidence = {
                "products": overlap,
                "supplier_price_signals": len(price),
                "margin_signals": len(margin),
            }
            if state is not None and getattr(state, "gross_margin_pct", None) is not None:
                evidence["business_gross_margin_pct"] = str(state.gross_margin_pct)

            situations.append(BusinessSituation(
                code="MARGIN_PRESSURE",
                title="Procurement costs are putting pressure on margin",
                severity="critical" if any(s.severity == "critical" for s in related) else "warning",
                confidence=Decimal("0.90"),
                signal_codes=_unique_codes(related),
                evidence=evidence,
                explanation=f"Supplier cost increases and thin margins overlap on {', '.join(overlap[:5])}.",
                recommended_next_step="Review supplier pricing and selling prices for the affected products.",
            ))

    supplier = by_code.get("SUPPLIER_CONCENTRATION", [])
    if supplier and price:
        supplier_names = sorted({
            _signal_evidence(s, "supplier")
            for s in supplier
            if _signal_evidence(s, "supplier")
        })
        affected = [
            s for s in price
            if _signal_evidence(s, "supplier") in supplier_names
        ]
        if affected and supplier_names:
            related = supplier + affected
            situations.append(BusinessSituation(
                code="SUPPLIER_DEPENDENCY_PRESSURE",
                title="Supplier dependency and price pressure overlap",
                severity="critical" if any(s.severity == "critical" for s in related) else "warning",
                confidence=Decimal("0.88"),
                signal_codes=_unique_codes(related),
                evidence={
                    "supplier": supplier_names[0],
                    "affected_suppliers": supplier_names,
                    "price_signals": len(affected),
                },
                explanation="A concentrated supplier relationship is also associated with a recent price increase.",
                recommended_next_step="Review alternative suppliers and negotiate current buying terms.",
            ))

    purchase_spikes = by_code.get("SUPPLIER_SPEND_SPIKE", [])
    demand = by_code.get("DEMAND_SPIKE", [])
    if purchase_spikes and demand:
        related = purchase_spikes + demand
        evidence = {
            "supplier_spend_spikes": len(purchase_spikes),
            "demand_spikes": len(demand),
        }
        if state is not None and getattr(state, "purchase_spend", None) is not None:
            evidence["purchase_spend"] = str(state.purchase_spend)

        situations.append(BusinessSituation(
            code="PROCUREMENT_DEMAND_PRESSURE",
            title="Purchasing and demand are both increasing",
            severity="warning",
            confidence=Decimal("0.82"),
            signal_codes=_unique_codes(related),
            evidence=evidence,
            explanation="Higher supplier spend coincides with materially higher product demand.",
            recommended_next_step="Check whether inventory and supplier lead times are sufficient for the increased demand.",
        ))

    receivables = by_code.get("RECEIVABLE_OVERDUE", [])
    payables = by_code.get("PAYABLE_OVERDUE", [])
    if receivables and payables:
        related = receivables + payables
        evidence = {
            "overdue_customer_accounts": len(receivables),
            "overdue_supplier_accounts": len(payables),
        }
        if state is not None:
            if getattr(state, "receivables_outstanding", None) is not None:
                evidence["receivables_outstanding"] = str(state.receivables_outstanding)
            if getattr(state, "payables_outstanding", None) is not None:
                evidence["payables_outstanding"] = str(state.payables_outstanding)

        situations.append(BusinessSituation(
            code="WORKING_CAPITAL_PRESSURE",
            title="Both customer collections and supplier payments need attention",
            severity="critical" if any(s.severity == "critical" for s in related) else "warning",
            confidence=Decimal("0.86"),
            signal_codes=_unique_codes(related),
            evidence=evidence,
            explanation="The business has overdue customer receivables while supplier obligations are also overdue.",
            recommended_next_step="Review near-term collections and supplier payment priorities together.",
        ))

    return situations
