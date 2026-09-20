from decimal import Decimal
from types import SimpleNamespace

from packages.analytics.business_brain.analysis import analyze_situation


def situation(code, evidence=None, confidence="0.90"):
    return SimpleNamespace(
        code=code,
        evidence=evidence or {},
        confidence=Decimal(confidence),
    )


def test_margin_pressure_exposes_root_cause_and_margin_impact():
    state = SimpleNamespace(gross_margin_pct=Decimal("8.5"))

    analysis = analyze_situation(
        situation(
            "MARGIN_PRESSURE",
            {
                "products": ["USB Connector"],
                "supplier_price_signals": 1,
                "margin_signals": 1,
            },
        ),
        state,
    )

    assert analysis.situation_code == "MARGIN_PRESSURE"
    assert analysis.root_causes[0].code == "SUPPLIER_COST_PRESSURE"
    assert analysis.root_causes[0].evidence["products"] == ["USB Connector"]
    assert analysis.impacts[0].metric == "gross_margin_pct"
    assert analysis.impacts[0].value == Decimal("8.5")


def test_working_capital_analysis_does_not_fabricate_impact():
    analysis = analyze_situation(
        situation(
            "WORKING_CAPITAL_PRESSURE",
            {
                "overdue_customer_accounts": 1,
                "overdue_supplier_accounts": 1,
            },
        ),
        SimpleNamespace(net_working_capital=None),
    )

    assert analysis.root_causes[0].code == "DUAL_WORKING_CAPITAL_PRESSURE"
    assert analysis.impacts[0].value is None
    assert "both sides" in analysis.impacts[0].description.lower()


def test_revenue_cost_squeeze_uses_state_expense_ratio():
    analysis = analyze_situation(
        situation(
            "REVENUE_COST_SQUEEZE",
            {
                "revenue_decline_signals": 1,
                "expense_spike_signals": 1,
            },
        ),
        SimpleNamespace(expense_to_revenue_pct=Decimal("22")),
    )

    assert analysis.root_causes[0].code == "REVENUE_DOWN_EXPENSES_UP"
    assert analysis.impacts[0].metric == "expense_to_revenue_pct"
    assert analysis.impacts[0].value == Decimal("22")
