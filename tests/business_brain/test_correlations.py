from decimal import Decimal
from types import SimpleNamespace

from packages.analytics.business_brain.correlations import correlate_signals


def signal(code: str, severity: str = "warning", evidence: dict | None = None):
    return SimpleNamespace(
        code=code,
        severity=severity,
        evidence=evidence or {},
    )


def test_margin_pressure_requires_product_overlap():
    signals = [
        signal("SUPPLIER_PRICE_INCREASE", evidence={"supplier": "Supplier A", "product": "Cable"}),
        signal("PRODUCT_MARGIN_DETERIORATION", evidence={"product": "Cable"}),
    ]

    situations = correlate_signals(signals)

    assert len(situations) == 1
    assert situations[0].code == "MARGIN_PRESSURE"
    assert situations[0].confidence == Decimal("0.90")
    assert "Cable" in situations[0].evidence["products"]


def test_margin_pressure_does_not_cross_products():
    signals = [
        signal("SUPPLIER_PRICE_INCREASE", evidence={"supplier": "Supplier A", "product": "Cable"}),
        signal("PRODUCT_MARGIN_DETERIORATION", evidence={"product": "Connector"}),
    ]

    assert correlate_signals(signals) == []


def test_margin_pressure_uses_canonical_state_as_supporting_evidence():
    signals = [
        signal("SUPPLIER_PRICE_INCREASE", evidence={"supplier": "Supplier A", "product": "Cable"}),
        signal("PRODUCT_MARGIN_DETERIORATION", evidence={"product": "Cable"}),
    ]
    state = SimpleNamespace(gross_margin_pct=Decimal("8.5"))

    situations = correlate_signals(signals, state)

    assert situations[0].evidence["business_gross_margin_pct"] == "8.5"


def test_situation_signal_codes_are_unique_and_stable():
    signals = [
        signal("SUPPLIER_PRICE_INCREASE", evidence={"supplier": "Supplier A", "product": "Cable"}),
        signal("SUPPLIER_PRICE_INCREASE", evidence={"supplier": "Supplier B", "product": "Cable"}),
        signal("PRODUCT_MARGIN_DETERIORATION", evidence={"product": "Cable"}),
    ]

    situation = correlate_signals(signals)[0]

    assert situation.signal_codes == [
        "SUPPLIER_PRICE_INCREASE",
        "PRODUCT_MARGIN_DETERIORATION",
    ]


def test_supplier_dependency_selection_is_deterministic():
    signals = [
        signal("SUPPLIER_CONCENTRATION", evidence={"supplier": "Zeta Supplies"}),
        signal("SUPPLIER_CONCENTRATION", evidence={"supplier": "Alpha Supplies"}),
        signal("SUPPLIER_PRICE_INCREASE", evidence={"supplier": "Alpha Supplies", "product": "Cable"}),
    ]

    situation = correlate_signals(signals)[0]

    assert situation.evidence["supplier"] == "Alpha Supplies"
    assert situation.evidence["affected_suppliers"] == ["Alpha Supplies", "Zeta Supplies"]


def test_working_capital_pressure_requires_both_sides():
    signals = [
        signal("RECEIVABLE_OVERDUE", severity="warning", evidence={"customer": "Customer A"}),
        signal("PAYABLE_OVERDUE", severity="critical", evidence={"supplier": "Supplier A"}),
    ]

    situations = correlate_signals(signals)

    assert len(situations) == 1
    assert situations[0].code == "WORKING_CAPITAL_PRESSURE"
    assert situations[0].severity == "critical"


def test_working_capital_situation_uses_state_totals_when_available():
    signals = [
        signal("RECEIVABLE_OVERDUE", evidence={"customer": "Customer A"}),
        signal("PAYABLE_OVERDUE", evidence={"supplier": "Supplier A"}),
    ]
    state = SimpleNamespace(
        receivables_outstanding=Decimal("12000"),
        payables_outstanding=Decimal("9000"),
        net_working_capital=Decimal("3000"),
    )

    situations = correlate_signals(signals, state)

    assert situations[0].evidence["receivables_outstanding"] == "12000"
    assert situations[0].evidence["payables_outstanding"] == "9000"
    assert situations[0].evidence["net_working_capital"] == "3000"


def test_procurement_demand_pressure_requires_both_signals():
    signals = [
        signal("SUPPLIER_SPEND_SPIKE", evidence={"supplier": "Supplier A"}),
        signal("DEMAND_SPIKE", evidence={"product": "Cable"}),
    ]

    situations = correlate_signals(signals)

    assert len(situations) == 1
    assert situations[0].code == "PROCUREMENT_DEMAND_PRESSURE"
    assert situations[0].confidence == Decimal("0.82")


def test_profitability_pressure_links_margin_and_expense_signals():
    signals = [
        signal("PRODUCT_MARGIN_DETERIORATION", evidence={"product": "Cable"}),
        signal("EXPENSE_SPIKE", evidence={"category": "Freight"}),
    ]
    state = SimpleNamespace(
        gross_profit=Decimal("30000"),
        total_expenses=Decimal("35000"),
        operating_surplus=Decimal("-5000"),
    )

    situations = correlate_signals(signals, state)

    assert len(situations) == 1
    assert situations[0].code == "PROFITABILITY_PRESSURE"
    assert situations[0].evidence["operating_surplus"] == "-5000"


def test_revenue_cost_squeeze_requires_revenue_decline_and_expense_spike():
    signals = [
        signal("REVENUE_DECLINE", evidence={"rule": "change <= -10%"}),
        signal("EXPENSE_SPIKE", evidence={"category": "Rent"}),
    ]
    state = SimpleNamespace(
        revenue=Decimal("80000"),
        revenue_change_pct=Decimal("-15"),
        expense_to_revenue_pct=Decimal("22"),
    )

    situations = correlate_signals(signals, state)

    assert len(situations) == 1
    assert situations[0].code == "REVENUE_COST_SQUEEZE"
    assert situations[0].severity == "warning"


def test_unrelated_signals_do_not_create_a_situation():
    signals = [
        signal("CUSTOMER_INACTIVE", evidence={"customer": "Customer A"}),
        signal("EXPENSE_SPIKE", evidence={"category": "Rent"}),
    ]

    assert correlate_signals(signals) == []
