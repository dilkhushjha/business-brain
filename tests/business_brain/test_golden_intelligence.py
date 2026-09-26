from __future__ import annotations

from datetime import date, timedelta

from packages.analytics.business_brain.context.builder import build_business_context
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import PurchaseModel, SaleModel


def _scenario_dates() -> tuple[str, str, str, date]:
    today = date.today()
    historical = today - timedelta(days=50)
    current = today - timedelta(days=10)
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
            "cost_price": 80,
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
    risk_codes = {risk.code for risk in context.risks}
    assert "MARGIN_RISK" in risk_codes
    assert "SUPPLIER_RISK" in risk_codes


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


def test_golden_working_capital_scenario_tracks_pressure_and_resolution(db_session, seeder):
    business = seeder.business(name="Golden Working Capital", industry="distribution")
    customer = seeder.customer(business.id, "Alpha Traders")
    supplier = seeder.supplier(business.id, "Prime Cables")
    product = seeder.product(business.id, "HDMI Cable 2M")

    sale = seeder.sale_with_line(
        business.id,
        product.id,
        customer_id=customer.id,
        days_ago=10,
        quantity=20,
        unit_price=100,
        due_days_ago=5,
        paid_amount=0,
    )
    purchase = seeder.purchase_with_line(
        business.id,
        product.id,
        supplier_id=supplier.id,
        days_ago=10,
        quantity=20,
        unit_cost=60,
        due_days_ago=5,
        paid_amount=0,
        invoice_number="PUR-WC-001",
    )
    db_session.commit()

    first = build_business_context(db_session, business.id, date.today())
    situation_codes = {s.code for s in first.situations}
    action_codes = {a.code for a in first.decision_actions}

    assert "RECEIVABLE_OVERDUE" in {s.code for s in first.signals}
    assert "PAYABLE_OVERDUE" in {s.code for s in first.signals}
    assert "WORKING_CAPITAL_PRESSURE" in situation_codes
    assert "REVIEW_WORKING_CAPITAL_PRESSURE" in action_codes

    history = next(h for h in first.situation_history if h.situation_code == "WORKING_CAPITAL_PRESSURE")
    assert history.status == "active"
    assert history.trend == "new"

    # Resolve both sides of the pressure and refresh the same business.
    sale.paid_amount = sale.total_amount
    purchase.paid_amount = purchase.total_amount
    db_session.commit()

    second = build_business_context(db_session, business.id, date.today())
    resolved = next(
        h for h in second.situation_history
        if h.situation_code == "WORKING_CAPITAL_PRESSURE"
    )
    assert resolved.status == "resolved"
    assert resolved.resolved_at == date.today()


def test_integrity_exceptions_qualify_business_conclusions(db_session, seeder):
    business = seeder.business(name="Golden Integrity Qualification", industry="distribution")
    seeder.product(business.id, "HDMI Cable 2M")
    seeder.customer(business.id, "Customer")

    persist_purchases(db_session, business.id, [{
        "invoice_number": "P-QUAL-001",
        "transaction_date": date.today().isoformat(),
        "product_name": "HDMI Cable 2M",
        "supplier_name": "Prime Cables",
        "quantity": 10,
        "unit_price": 80,
        "total_amount": 800,
    }])
    persist_sales(db_session, business.id, [{
        "invoice_number": "S-QUAL-001",
        "transaction_date": date.today().isoformat(),
        "product_name": "HDMI Cable 2M",
        "customer_name": "Customer",
        "quantity": 5,
        "unit_price": 75,
        "total_amount": 375,
        "cost_price": 80,
    }])

    from packages.shared.database.models import ProductModel
    db_session.add(ProductModel(business_id=business.id, name=" hdmi  cable  2m "))
    db_session.commit()

    context = build_business_context(db_session, business.id, date.today())

    assert context.integrity["status"] == "attention_required"
    assert "data_quality" in context.integrity["affected_domains"]

    for situation in context.situations:
        if situation.code in {"MARGIN_PRESSURE", "PROFITABILITY_PRESSURE", "REVENUE_COST_SQUEEZE"}:
            assert situation.confidence <= 0.65
            assert situation.evidence["integrity_status"] == "attention_required"
            assert "integrity issues" in situation.explanation


def test_working_capital_situation_flows_through_history_and_decision_support(db_session, seeder):
    business = seeder.business(name="Golden Working Capital", industry="distribution")
    customer = seeder.customer(business.id, "Alpha Traders")
    supplier = seeder.supplier(business.id, "Prime Cables")
    product = seeder.product(business.id, "HDMI Cable 2M")

    seeder.sale_with_line(
        business.id,
        product.id,
        customer_id=customer.id,
        days_ago=45,
        quantity=10,
        unit_price=100,
        due_days_ago=30,
        paid_amount=0,
    )
    seeder.purchase_with_line(
        business.id,
        product.id,
        supplier_id=supplier.id,
        days_ago=45,
        quantity=20,
        unit_cost=50,
        due_days_ago=30,
        paid_amount=0,
        invoice_number="PUR-WC-001",
    )
    db_session.commit()

    first = build_business_context(db_session, business.id, date.today())
    situation_codes = {item.code for item in first.situations}
    action_codes = {item.code for item in first.decision_actions}

    assert "WORKING_CAPITAL_PRESSURE" in situation_codes
    assert "REVIEW_WORKING_CAPITAL_PRESSURE" in action_codes

    history = next(item for item in first.situation_history if item.situation_code == "WORKING_CAPITAL_PRESSURE")
    assert history.status == "active"
    assert history.trend == "new"

    # Settle the same documents and refresh Business Brain.
    db_session.query(SaleModel).filter(
        SaleModel.business_id == business.id,
        SaleModel.customer_id == customer.id,
    ).update({SaleModel.paid_amount: SaleModel.total_amount}, synchronize_session=False)
    db_session.query(PurchaseModel).filter(
        PurchaseModel.business_id == business.id,
        PurchaseModel.supplier_id == supplier.id,
    ).update({PurchaseModel.paid_amount: PurchaseModel.total_amount}, synchronize_session=False)
    db_session.commit()

    second = build_business_context(db_session, business.id, date.today())
    resolved = next(item for item in second.situation_history if item.situation_code == "WORKING_CAPITAL_PRESSURE")
    assert resolved.status == "resolved"
    assert resolved.trend == "resolved"


def test_golden_working_capital_scenario_produces_action_chain(db_session, seeder):
    business = seeder.business(name="Golden Working Capital", industry="distribution")

    purchases = [{
        "invoice_number": "P-WC-001",
        "transaction_date": "2026-08-01",
        "due_date": "2026-08-15",
        "product_name": "Cable",
        "supplier_name": "Prime Cables",
        "quantity": 20,
        "unit_price": 50,
        "total_amount": 1000,
        "paid_amount": 0,
    }]
    sales = [{
        "invoice_number": "S-WC-001",
        "transaction_date": "2026-08-02",
        "due_date": "2026-08-16",
        "product_name": "Cable",
        "customer_name": "Alpha Traders",
        "quantity": 10,
        "unit_price": 100,
        "total_amount": 1000,
        "paid_amount": 0,
    }]

    persist_purchases(db_session, business.id, purchases)
    persist_sales(db_session, business.id, sales)
    db_session.commit()

    context = build_business_context(db_session, business.id, date(2026, 9, 20))

    signal_codes = {signal.code for signal in context.signals}
    situation_codes = {situation.code for situation in context.situations}
    action_codes = {action.code for action in context.decision_actions}

    assert "RECEIVABLE_OVERDUE" in signal_codes
    assert "PAYABLE_OVERDUE" in signal_codes
    assert "WORKING_CAPITAL_PRESSURE" in situation_codes
    assert "REVIEW_WORKING_CAPITAL_PRESSURE" in action_codes

    situation = next(s for s in context.situations if s.code == "WORKING_CAPITAL_PRESSURE")
    assert situation.evidence["receivables_outstanding"] == "1000.0"
    assert situation.evidence["payables_outstanding"] == "1000.0"

    priority = next(p for p in context.priorities if p.situation_code == "WORKING_CAPITAL_PRESSURE")
    action = next(a for a in context.decision_actions if a.situation_code == "WORKING_CAPITAL_PRESSURE")
    assert action.priority_score == priority.score
    assert action.confidence == situation.confidence
    assert action.actions
