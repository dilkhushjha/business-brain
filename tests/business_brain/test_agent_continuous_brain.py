from datetime import date, timedelta

from packages.agent.business_brain.agent.service import answer
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales


def test_agent_answers_from_continuous_business_brain_state(db_session, seeder):
    business = seeder.business(name="Golden Agent Acceptance", industry="distribution")
    today = date.today()

    persist_purchases(
        db_session,
        business.id,
        [
            {
                "invoice_number": "P-HIST",
                "transaction_date": (today - timedelta(days=50)).isoformat(),
                "product_name": "HDMI Cable 2M",
                "supplier_name": "Prime Cables",
                "quantity": 10,
                "unit_price": 40,
                "total_amount": 400,
            },
            {
                "invoice_number": "P-CUR",
                "transaction_date": (today - timedelta(days=10)).isoformat(),
                "product_name": "HDMI Cable 2M",
                "supplier_name": "Prime Cables",
                "quantity": 150,
                "unit_price": 80,
                "total_amount": 12000,
            },
        ],
    )
    persist_sales(
        db_session,
        business.id,
        [
            {
                "invoice_number": "S-CUR",
                "transaction_date": (today - timedelta(days=20)).isoformat(),
                "product_name": "HDMI Cable 2M",
                "customer_name": "Alpha Traders",
                "quantity": 60,
                "unit_price": 75,
                "total_amount": 4500,
                "cost_price": 80,
            }
        ],
    )
    db_session.commit()

    result = answer(
        db_session,
        business.id,
        "What is causing my margin pressure?",
        today,
    )

    assert result.intent == "root_cause"
    assert "margin" in result.answer.lower()
    assert result.confidence != "unknown"
    assert result.evidence
    assert result.signals
    assert result.decision_actions
    assert result.situation_history
    assert "contributing factor" in result.answer.lower()
    assert "margin" in result.answer.lower()
