from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BusinessState:
    """Canonical cross-domain snapshot used by Business Brain reasoning."""

    revenue: Decimal | None = None
    revenue_change_pct: Decimal | None = None
    gross_profit: Decimal | None = None
    gross_margin_pct: Decimal | None = None
    purchase_spend: Decimal | None = None
    supplier_spend_share_pct: Decimal | None = None
    receivables_outstanding: Decimal | None = None
    payables_outstanding: Decimal | None = None
    total_expenses: Decimal | None = None
    customer_concentration_pct: Decimal | None = None
    supplier_concentration_pct: Decimal | None = None
    signal_count: int = 0
    critical_signal_count: int = 0
    warning_signal_count: int = 0
    metadata: dict[str, Any] | None = None


def build_business_state(
    *,
    kpis: list[Any],
    margin: dict[str, Any],
    receivables: dict[str, Any],
    payables: dict[str, Any],
    purchase_risk: dict[str, Any],
    customer_concentration: dict[str, Any],
    supplier_concentration: dict[str, Any],
    expenses: dict[str, Any],
    signals: list[Any],
) -> BusinessState:
    """Build one coherent business snapshot from already-computed evidence.

    Missing source data remains None rather than being interpreted as zero.
    """

    revenue_kpi = next((k for k in kpis if k.name == "revenue"), None)
    change = getattr(revenue_kpi, "change", None) if revenue_kpi else None

    critical = sum(1 for s in signals if getattr(s, "severity", None) == "critical")
    warning = sum(1 for s in signals if getattr(s, "severity", None) in {"warning", "high"})

    return BusinessState(
        revenue=Decimal(str(revenue_kpi.value)) if revenue_kpi else None,
        revenue_change_pct=Decimal(str(change)) if change is not None else None,
        gross_profit=Decimal(str(margin["gross_profit"])) if margin.get("gross_profit") is not None else None,
        gross_margin_pct=Decimal(str(margin["gross_margin_pct"])) if margin.get("gross_margin_pct") is not None else None,
        purchase_spend=Decimal(str(purchase_risk["total_spend"])) if purchase_risk.get("total_spend") else None,
        supplier_spend_share_pct=Decimal(str(purchase_risk["top_share_pct"])) if purchase_risk.get("total_spend") else None,
        receivables_outstanding=Decimal(str(receivables["outstanding"])) if receivables.get("outstanding") else None,
        payables_outstanding=Decimal(str(payables["outstanding"])) if payables.get("outstanding") else None,
        total_expenses=Decimal(str(expenses["total"])) if expenses.get("total") else None,
        customer_concentration_pct=Decimal(str(customer_concentration["top_share_pct"])) if customer_concentration.get("top_customers") else None,
        supplier_concentration_pct=Decimal(str(supplier_concentration["top_share_pct"])) if supplier_concentration.get("top_suppliers") else None,
        signal_count=len(signals),
        critical_signal_count=critical,
        warning_signal_count=warning,
        metadata={
            "top_supplier_by_spend": purchase_risk.get("top_supplier"),
            "top_customer_share_pct": customer_concentration.get("top_share_pct"),
            "top_supplier_share_pct": supplier_concentration.get("top_share_pct"),
            "expense_categories": expenses.get("by_category", {}),
        },
    )
