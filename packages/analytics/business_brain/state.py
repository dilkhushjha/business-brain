from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BusinessState:
    """Canonical cross-domain snapshot used by Business Brain reasoning.

    Derived economic fields are only populated when their source inputs exist.
    They describe accounting/working-capital relationships, not bank cash.
    """

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

    # Cross-domain economic relationships.
    operating_surplus: Decimal | None = None
    net_working_capital: Decimal | None = None
    purchase_to_revenue_pct: Decimal | None = None
    expense_to_revenue_pct: Decimal | None = None

    signal_count: int = 0
    critical_signal_count: int = 0
    warning_signal_count: int = 0
    metadata: dict[str, Any] | None = None


def _decimal(value: Any) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def _ratio_pct(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return (numerator / denominator) * Decimal("100")


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
    Derived relationships are calculated only when their source values are
    available. This state does not estimate bank cash.
    """

    revenue_kpi = next((k for k in kpis if k.name == "revenue"), None)
    revenue = _decimal(revenue_kpi.value) if revenue_kpi else None
    change = getattr(revenue_kpi, "change", None) if revenue_kpi else None

    gross_profit = _decimal(margin.get("gross_profit"))
    purchase_spend = _decimal(purchase_risk.get("total_spend"))
    receivables_outstanding = _decimal(receivables.get("outstanding"))
    payables_outstanding = _decimal(payables.get("outstanding"))
    total_expenses = _decimal(expenses.get("total"))

    operating_surplus = (
        gross_profit - total_expenses
        if gross_profit is not None and total_expenses is not None
        else None
    )
    net_working_capital = (
        receivables_outstanding - payables_outstanding
        if receivables_outstanding is not None and payables_outstanding is not None
        else None
    )

    critical = sum(1 for s in signals if getattr(s, "severity", None) == "critical")
    warning = sum(1 for s in signals if getattr(s, "severity", None) in {"warning", "high"})

    return BusinessState(
        revenue=revenue,
        revenue_change_pct=_decimal(change),
        gross_profit=gross_profit,
        gross_margin_pct=_decimal(margin.get("gross_margin_pct")),
        purchase_spend=purchase_spend,
        supplier_spend_share_pct=(
            _decimal(purchase_risk.get("top_share_pct"))
            if purchase_spend is not None else None
        ),
        receivables_outstanding=receivables_outstanding,
        payables_outstanding=payables_outstanding,
        total_expenses=total_expenses,
        customer_concentration_pct=(
            _decimal(customer_concentration.get("top_share_pct"))
            if customer_concentration.get("top_customers") else None
        ),
        supplier_concentration_pct=(
            _decimal(supplier_concentration.get("top_share_pct"))
            if supplier_concentration.get("top_suppliers") else None
        ),
        operating_surplus=operating_surplus,
        net_working_capital=net_working_capital,
        purchase_to_revenue_pct=_ratio_pct(purchase_spend, revenue),
        expense_to_revenue_pct=_ratio_pct(total_expenses, revenue),
        signal_count=len(signals),
        critical_signal_count=critical,
        warning_signal_count=warning,
        metadata={
            "top_supplier_by_spend": purchase_risk.get("top_supplier"),
            "top_customer_share_pct": customer_concentration.get("top_share_pct"),
            "top_supplier_share_pct": supplier_concentration.get("top_share_pct"),
            "expense_categories": expenses.get("by_category", {}),
            "cash_position": None,
            "cash_position_note": "Not estimated without payment/cash-ledger evidence.",
        },
    )
