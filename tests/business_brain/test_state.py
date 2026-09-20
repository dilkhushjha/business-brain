from decimal import Decimal
from types import SimpleNamespace

from packages.analytics.business_brain.state import build_business_state


def test_business_state_derives_economic_relationships():
    state = build_business_state(
        kpis=[SimpleNamespace(name="revenue", value=Decimal("100000"), change=Decimal("12"))],
        margin={"gross_profit": Decimal("30000"), "gross_margin_pct": Decimal("30")},
        receivables={"outstanding": Decimal("25000")},
        payables={"outstanding": Decimal("15000")},
        purchase_risk={"total_spend": Decimal("60000"), "top_share_pct": Decimal("55"), "top_supplier": "Supplier A"},
        customer_concentration={"top_customers": [{"name": "Customer A"}], "top_share_pct": Decimal("40")},
        supplier_concentration={"top_suppliers": [{"name": "Supplier A"}], "top_share_pct": Decimal("55")},
        expenses={"total": Decimal("10000"), "by_category": {"Rent": Decimal("4000")}},
        signals=[],
    )

    assert state.operating_surplus == Decimal("20000")
    assert state.net_working_capital == Decimal("10000")
    assert state.purchase_to_revenue_pct == Decimal("60")
    assert state.expense_to_revenue_pct == Decimal("10")


def test_business_state_does_not_invent_cash():
    state = build_business_state(
        kpis=[],
        margin={},
        receivables={},
        payables={},
        purchase_risk={},
        customer_concentration={},
        supplier_concentration={},
        expenses={},
        signals=[],
    )

    assert state.operating_surplus is None
    assert state.net_working_capital is None
    assert state.metadata["cash_position"] is None
    assert "Not estimated" in state.metadata["cash_position_note"]


def test_business_state_does_not_divide_by_missing_or_zero_revenue():
    state = build_business_state(
        kpis=[SimpleNamespace(name="revenue", value=Decimal("0"), change=None)],
        margin={"gross_profit": Decimal("100"), "gross_margin_pct": None},
        receivables={},
        payables={},
        purchase_risk={"total_spend": Decimal("50")},
        customer_concentration={},
        supplier_concentration={},
        expenses={"total": Decimal("20")},
        signals=[],
    )

    assert state.purchase_to_revenue_pct is None
    assert state.expense_to_revenue_pct is None
