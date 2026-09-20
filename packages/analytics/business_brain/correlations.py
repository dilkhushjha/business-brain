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


def correlate_signals(signals: list[Any], state: Any | None = None) -> list[BusinessSituation]:
    """Collapse related signals into evidence-backed cross-domain situations.

    Correlation is deliberately conservative: a situation requires specific
    signal combinations and never invents a causal relationship when evidence
    is absent.
    """
    by_code = {}
    for signal in signals:
        by_code.setdefault(signal.code, []).append(signal)

    situations: list[BusinessSituation] = []

    price = by_code.get("SUPPLIER_PRICE_INCREASE", [])
    margin = by_code.get("PRODUCT_MARGIN_DETERIORATION", [])
    if price and margin:
        price_products = {(s.evidence.get("product"), s.evidence.get("supplier")) for s in price}
        margin_products = {s.evidence.get("product") for s in margin}
        overlap = [p for p, _ in price_products if p in margin_products]
        if overlap:
            situations.append(BusinessSituation(
                code="MARGIN_PRESSURE",
                title="Procurement costs are putting pressure on margin",
                severity="critical" if any(s.severity == "critical" for s in price + margin) else "warning",
                confidence=Decimal("0.90"),
                signal_codes=[s.code for s in price + margin],
                evidence={"products": overlap, "supplier_price_signals": len(price), "margin_signals": len(margin)},
                explanation=f"Supplier cost increases and thin margins overlap on {', '.join(overlap[:5])}.",
                recommended_next_step="Review supplier pricing and selling prices for the affected products.",
            ))

    supplier = by_code.get("SUPPLIER_CONCENTRATION", [])
    if supplier and price:
        supplier_names = {s.evidence.get("supplier") for s in supplier}
        affected = [s for s in price if s.evidence.get("supplier") in supplier_names]
        if affected:
            situations.append(BusinessSituation(
                code="SUPPLIER_DEPENDENCY_PRESSURE",
                title="Supplier dependency and price pressure overlap",
                severity="critical" if any(s.severity == "critical" for s in supplier + affected) else "warning",
                confidence=Decimal("0.88"),
                signal_codes=[s.code for s in supplier + affected],
                evidence={"supplier": next(iter(supplier_names)), "price_signals": len(affected)},
                explanation="A concentrated supplier relationship is also associated with a recent price increase.",
                recommended_next_step="Review alternative suppliers and negotiate current buying terms.",
            ))

    purchase_spikes = by_code.get("SUPPLIER_SPEND_SPIKE", [])
    demand = by_code.get("DEMAND_SPIKE", [])
    if purchase_spikes and demand:
        situations.append(BusinessSituation(
            code="PROCUREMENT_DEMAND_PRESSURE",
            title="Purchasing and demand are both increasing",
            severity="warning",
            confidence=Decimal("0.82"),
            signal_codes=[s.code for s in purchase_spikes + demand],
            evidence={"supplier_spend_spikes": len(purchase_spikes), "demand_spikes": len(demand)},
            explanation="Higher supplier spend coincides with materially higher product demand.",
            recommended_next_step="Check whether inventory and supplier lead times are sufficient for the increased demand.",
        ))

    receivables = by_code.get("RECEIVABLE_OVERDUE", [])
    payables = by_code.get("PAYABLE_OVERDUE", [])
    if receivables and payables:
        situations.append(BusinessSituation(
            code="WORKING_CAPITAL_PRESSURE",
            title="Both customer collections and supplier payments need attention",
            severity="critical" if any(s.severity == "critical" for s in receivables + payables) else "warning",
            confidence=Decimal("0.86"),
            signal_codes=[s.code for s in receivables + payables],
            evidence={"overdue_customer_accounts": len(receivables), "overdue_supplier_accounts": len(payables)},
            explanation="The business has overdue customer receivables while supplier obligations are also overdue.",
            recommended_next_step="Review near-term collections and supplier payment priorities together.",
        ))

    return situations
