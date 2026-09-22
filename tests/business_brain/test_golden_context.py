from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from packages.analytics.business_brain.context.builder import build_business_context
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import BusinessModel

FIXTURE = Path(__file__).parents[1] / "fixtures" / "golden_sme_distribution.json"


def test_golden_dataset_builds_coherent_business_context(db_session):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    business = BusinessModel(id=uuid4(), name=data["business"]["name"], industry=data["business"]["industry"])
    db_session.add(business)
    db_session.commit()

    sales = [
        {
            "invoice_number": row["invoice_number"],
            "transaction_date": "2026-09-01",
            "product_name": row["product"],
            "customer_name": row["customer"],
            "quantity": row["quantity"],
            "unit_price": row["unit_price"],
            "total_amount": row["total"],
        }
        for row in data["sales"]
    ]
    purchases = [
        {
            "invoice_number": row["invoice_number"],
            "transaction_date": "2026-08-28",
            "product_name": row["product"],
            "supplier_name": row["supplier"],
            "quantity": row["quantity"],
            "unit_price": row["unit_cost"],
            "total_amount": row["total"],
        }
        for row in data["purchases"]
    ]

    persist_sales(db_session, business.id, sales)
    persist_purchases(db_session, business.id, purchases)
    db_session.commit()

    context = build_business_context(
        db_session,
        business.id,
        __import__("datetime").date(2026, 9, 20),
    )

    assert context.business_id == business.id
    assert context.evidence
    assert context.state is not None
    assert context.state.revenue is not None
    assert context.state.purchase_spend is not None
    assert context.state.metadata["cash_position"] is None
    assert isinstance(context.signals, list)
    assert isinstance(context.situations, list)
    assert isinstance(context.analyses, list)
    assert isinstance(context.priorities, list)
    assert isinstance(context.decision_actions, list)
    assert isinstance(context.situation_history, list)
    assert isinstance(context.risks, list)
