from __future__ import annotations

from datetime import date, timedelta
from packages.analytics.business_brain.context.builder import build_business_context
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales


def test_business_context_orders_situations_by_priority(db_session, seeder):
    business = seeder.business(name="Golden Priority Ordering", industry="distribution")
    as_of = date.today()
    historical_date = (as_of - timedelta(days=50)).isoformat()
    current_date = (as_of - timedelta(days=10)).isoformat()
    sale_date = (as_of - timedelta(days=20)).isoformat()

    persist_purchases(db_session, business.id, [
        {"invoice_number": "P-H-1", "transaction_date": historical_date, "product_name": "HDMI", "supplier_name": "Prime", "quantity": 10, "unit_price": 40, "total_amount": 400},
        {"invoice_number": "P-C-1", "transaction_date": current_date, "product_name": "HDMI", "supplier_name": "Prime", "quantity": 150, "unit_price": 80, "total_amount": 12000},
    ])
    persist_sales(db_session, business.id, [
        {"invoice_number": "S-1", "transaction_date": sale_date, "product_name": "HDMI", "customer_name": "Alpha", "quantity": 60, "unit_price": 75, "total_amount": 4500, "cost_price": 80},
    ])
    db_session.commit()

    context = build_business_context(db_session, business.id, as_of)
    scores = {item.situation_code: item.score for item in context.priorities}
    ordered_scores = [scores[item.code] for item in context.situations]

    assert ordered_scores == sorted(ordered_scores, reverse=True)
    assert context.situations
    assert context.situations[0].code == max(scores, key=scores.get)
