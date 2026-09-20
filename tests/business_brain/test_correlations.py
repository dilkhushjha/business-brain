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


def test_working_capital_pressure_requires_both_sides():
    signals = [
        signal("RECEIVABLE_OVERDUE", severity="warning", evidence={"customer": "Customer A"}),
        signal("PAYABLE_OVERDUE", severity="critical", evidence={"supplier": "Supplier A"}),
    ]

    situations = correlate_signals(signals)

    assert len(situations) == 1
    assert situations[0].code == "WORKING_CAPITAL_PRESSURE"
    assert situations[0].severity == "critical"


def test_procurement_demand_pressure_requires_both_signals():
    signals = [
        signal("SUPPLIER_SPEND_SPIKE", evidence={"supplier": "Supplier A"}),
        signal("DEMAND_SPIKE", evidence={"product": "Cable"}),
    ]

    situations = correlate_signals(signals)

    assert len(situations) == 1
    assert situations[0].code == "PROCUREMENT_DEMAND_PRESSURE"
    assert situations[0].confidence == Decimal("0.82")


def test_unrelated_signals_do_not_create_a_situation():
    signals = [
        signal("CUSTOMER_INACTIVE", evidence={"customer": "Customer A"}),
        signal("EXPENSE_SPIKE", evidence={"category": "Rent"}),
    ]

    assert correlate_signals(signals) == []
