from __future__ import annotations

from datetime import date, timedelta

from packages.analytics.business_brain.context.builder import build_business_context
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales


def _scenario_dates() -> tuple[str, str, str, date]:
    today = date.today()
    historical = today - timedelta(days=55)
    current = today - timedelta(days=25)
    sale = today - timedelta(days=20)
    return historical.isoformat(), current.isoformat(), sale.isoformat(), today


def test_golden_intelligence_scenario_produces_explainable_chain(db_session, seeder):
    business = seeder.business(name="Golden Intelligence Scenario", industry="distribution")
    historical_date, current_date, sale_date, as_of = _scenario_dates()

    # Same supplier/product across two periods: this creates a real, comparable
    # procurement-cost increase rather than a synthetic signal.
    purchases = [
        {
            "invoice_number": "P-HIST-001",
            "transaction_date": historical_date,
            "product_name": "HDMI Cable 2M",
            "supplier_name": "Prime Cables",
            "quantity": 10,
            "unit_price": 40,
            "total_amount": 400,
        },
        {
            "invoice_number": "P-CUR-001",
            "transaction_date": current_date,
            "product_name": "HDMI Cable 2M",
            "supplier_name": "Prime Cables",
            "quantity": 150,
            "unit_price": 80,
            "total_amount": 12000,
        },
    ]
    sales = [
        {
            "invoice_number": "S-CUR-001",
            "transaction_date": sale_date,
            "product_name": "HDMI Cable 2M",
            "customer_name": "Alpha Traders",
            "quantity": 60,
            "unit_price": 75,
            "total_amount": 4500,
        }
    ]

    persist_purchases(db_session, business.id, purchases)
    persist_sales(db_session, business.id, sales)
    db_session.commit()

    context = build_business_context(db_session, business.id, as_of)

    signal_codes = {signal.code for signal in context.signals}
    situation_codes = {situation.code for situation in context.situations}
    action_codes = {action.code for action in context.decision_actions}

    assert "PRODUCT_MARGIN_DETERIORATION" in signal_codes
    assert "SUPPLIER_PRICE_INCREASE" in signal_codes
    assert "SUPPLIER_CONCENTRATION" in signal_codes

    assert "MARGIN_PRESSURE" in situation_codes
    assert "SUPPLIER_DEPENDENCY_PRESSURE" in situation_codes

    assert "INVESTIGATE_MARGIN_PRESSURE" in action_codes
    assert "REDUCE_SUPPLIER_DEPENDENCY" in action_codes

    margin = next(a for a in context.analyses if a.situation_code == "MARGIN_PRESSURE")
    assert margin.root_causes
    assert margin.impacts

    priority = next(p for p in context.priorities if p.situation_code == "MARGIN_PRESSURE")
    action = next(a for a in context.decision_actions if a.situation_code == "MARGIN_PRESSURE")
    assert action.priority_score == priority.score
    assert action.confidence == next(
        s.confidence for s in context.situations if s.code == "MARGIN_PRESSURE"
    )
    assert action.evidence
    assert action.actions


def test_golden_intelligence_scenario_does_not_invent_cash(db_session, seeder):
    business = seeder.business(name="Golden Cash Guard", industry="distribution")
    _, current_date, sale_date, as_of = _scenario_dates()

    persist_purchases(
        db_session,
        business.id,
        [
            {
                "invoice_number": "P-001",
                "transaction_date": current_date,
                "product_name": "Cable",
                "supplier_name": "Supplier",
                "quantity": 10,
                "unit_price": 50,
                "total_amount": 500,
            }
        ],
    )
    persist_sales(
        db_session,
        business.id,
        [
            {
                "invoice_number": "S-001",
                "transaction_date": sale_date,
                "product_name": "Cable",
                "customer_name": "Customer",
                "quantity": 2,
                "unit_price": 100,
                "total_amount": 200,
            }
        ],
    )
    db_session.commit()

    context = build_business_context(db_session, business.id, as_of)

    assert context.state.metadata["cash_position"] is None
    assert "Not estimated" in context.state.metadata["cash_position_note"]
