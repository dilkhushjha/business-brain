from datetime import date

from packages.analytics.business_brain.context.builder import build_business_context
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases


def test_supplier_intelligence_respects_context_as_of_date(db_session, seeder):
    business = seeder.business(name="As Of Supplier Test", industry="distribution")

    persist_purchases(
        db_session,
        business.id,
        [
            {
                "invoice_number": "P-HIST",
                "transaction_date": "2026-04-10",
                "product_name": "Cable",
                "supplier_name": "Prime Cables",
                "quantity": 10,
                "unit_price": 40,
                "total_amount": 400,
            },
            {
                "invoice_number": "P-FUTURE",
                "transaction_date": "2026-12-10",
                "product_name": "Cable",
                "supplier_name": "Prime Cables",
                "quantity": 100,
                "unit_price": 80,
                "total_amount": 8000,
            },
        ],
    )
    db_session.commit()

    context = build_business_context(db_session, business.id, date(2026, 6, 30))

    assert context.state.purchase_spend == 400
    assert context.evidence
    supplier_evidence = [
        e for e in context.evidence if e.source == "purchase_risk_engine"
    ]
    assert supplier_evidence
    assert supplier_evidence[0].value == 100
