from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class RootCause:
    code: str
    title: str
    confidence: Decimal
    evidence: dict[str, Any]


@dataclass(frozen=True)
class BusinessImpact:
    metric: str
    value: Decimal | None
    unit: str | None
    direction: str
    description: str


@dataclass(frozen=True)
class SituationAnalysis:
    situation_code: str
    root_causes: list[RootCause]
    impacts: list[BusinessImpact]


def _decimal(value: Any) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def analyze_situation(situation: Any, state: Any | None = None) -> SituationAnalysis:
    """Explain a detected situation using only evidence already available.

    This layer deliberately does not invent dollar impacts. Where a direct
    financial metric exists in BusinessState it is surfaced; otherwise the
    impact remains qualitative and explicitly evidence-backed.
    """
    evidence = situation.evidence or {}
    code = situation.code
    root_causes: list[RootCause] = []
    impacts: list[BusinessImpact] = []

    if code == "MARGIN_PRESSURE":
        products = evidence.get("products", [])
        root_causes.append(RootCause(
            code="SUPPLIER_COST_PRESSURE",
            title="Higher supplier costs overlap with thin product margins",
            confidence=situation.confidence,
            evidence={
                "products": products,
                "supplier_price_signals": evidence.get("supplier_price_signals", 0),
                "margin_signals": evidence.get("margin_signals", 0),
            },
        ))
        gross_margin = _decimal(getattr(state, "gross_margin_pct", None)) if state else None
        impacts.append(BusinessImpact(
            metric="gross_margin_pct",
            value=gross_margin,
            unit="percent",
            direction="downward_pressure",
            description=(
                f"Current business gross margin is {gross_margin}%."
                if gross_margin is not None
                else "Gross margin is under pressure, but no current business-level margin value is available."
            ),
        ))

    elif code == "SUPPLIER_DEPENDENCY_PRESSURE":
        supplier = evidence.get("supplier")
        root_causes.append(RootCause(
            code="CONCENTRATED_SUPPLIER",
            title="Purchase dependence is concentrated in a supplier also raising prices",
            confidence=situation.confidence,
            evidence={
                "supplier": supplier,
                "affected_suppliers": evidence.get("affected_suppliers", []),
                "price_signals": evidence.get("price_signals", 0),
            },
        ))
        share = _decimal(getattr(state, "supplier_concentration_pct", None)) if state else None
        impacts.append(BusinessImpact(
            metric="supplier_concentration_pct",
            value=share,
            unit="percent",
            direction="concentration",
            description=(
                f"Top supplier concentration is {share}%."
                if share is not None
                else "Supplier dependency is concentrated, but the current concentration percentage is unavailable."
            ),
        ))

    elif code == "PROCUREMENT_DEMAND_PRESSURE":
        root_causes.append(RootCause(
            code="DEMAND_DRIVEN_PROCUREMENT",
            title="Higher purchasing coincides with higher demand",
            confidence=situation.confidence,
            evidence={
                "supplier_spend_spikes": evidence.get("supplier_spend_spikes", 0),
                "demand_spikes": evidence.get("demand_spikes", 0),
            },
        ))
        spend = _decimal(getattr(state, "purchase_spend", None)) if state else None
        impacts.append(BusinessImpact(
            metric="purchase_spend",
            value=spend,
            unit="currency",
            direction="upward",
            description=(
                f"Purchase spend is {spend}."
                if spend is not None
                else "Procurement activity is increasing alongside demand."
            ),
        ))

    elif code == "WORKING_CAPITAL_PRESSURE":
        root_causes.append(RootCause(
            code="DUAL_WORKING_CAPITAL_PRESSURE",
            title="Overdue customer collections and supplier obligations are occurring together",
            confidence=situation.confidence,
            evidence={
                "overdue_customer_accounts": evidence.get("overdue_customer_accounts", 0),
                "overdue_supplier_accounts": evidence.get("overdue_supplier_accounts", 0),
            },
        ))
        nwc = _decimal(getattr(state, "net_working_capital", None)) if state else _decimal(evidence.get("net_working_capital"))
        impacts.append(BusinessImpact(
            metric="net_working_capital",
            value=nwc,
            unit="currency",
            direction="working_capital",
            description=(
                f"Receivables less payables are {nwc}."
                if nwc is not None
                else "Both sides of the working-capital cycle require attention."
            ),
        ))

    elif code == "PROFITABILITY_PRESSURE":
        root_causes.append(RootCause(
            code="MARGIN_AND_EXPENSE_PRESSURE",
            title="Thin product margins coincide with higher operating expenses",
            confidence=situation.confidence,
            evidence={
                "margin_signals": evidence.get("margin_signals", 0),
                "expense_spikes": evidence.get("expense_spikes", 0),
            },
        ))
        surplus = _decimal(getattr(state, "operating_surplus", None)) if state else _decimal(evidence.get("operating_surplus"))
        impacts.append(BusinessImpact(
            metric="operating_surplus",
            value=surplus,
            unit="currency",
            direction="downward_pressure",
            description=(
                f"Operating surplus is {surplus}."
                if surplus is not None
                else "Profitability is under pressure, but no operating-surplus value is available."
            ),
        ))

    elif code == "REVENUE_COST_SQUEEZE":
        root_causes.append(RootCause(
            code="REVENUE_DOWN_EXPENSES_UP",
            title="Revenue decline is occurring while operating expenses increase",
            confidence=situation.confidence,
            evidence={
                "revenue_decline_signals": evidence.get("revenue_decline_signals", 0),
                "expense_spike_signals": evidence.get("expense_spike_signals", 0),
            },
        ))
        ratio = _decimal(getattr(state, "expense_to_revenue_pct", None)) if state else _decimal(evidence.get("expense_to_revenue_pct"))
        impacts.append(BusinessImpact(
            metric="expense_to_revenue_pct",
            value=ratio,
            unit="percent",
            direction="upward_pressure",
            description=(
                f"Expenses represent {ratio}% of revenue."
                if ratio is not None
                else "The cost base is rising relative to declining revenue."
            ),
        ))

    return SituationAnalysis(
        situation_code=code,
        root_causes=root_causes,
        impacts=impacts,
    )
