from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from packages.analytics.business_brain.context.builder import build_business_context
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import BusinessModel

FIXTURE = Path(__file__).parents[1] / "fixtures" / "sme_scenario_matrix.json"


def _business(db_session, name: str, industry: str) -> BusinessModel:
    business = BusinessModel(id=uuid4(), name=name, industry=industry)
    db_session.add(business)
    db_session.commit()
    return business


def _date(days_ago: int) -> str:
    return (date.today() - timedelta(days=days_ago)).isoformat()


def _seed_scenario(db_session, scenario_id: str) -> BusinessModel:
    business = _business(
        db_session,
        name=f"Scenario {scenario_id}",
        industry="distribution",
    )

    if scenario_id == "clean":
        persist_purchases(
            db_session,
            business.id,
            [{
                "invoice_number": "P-CLEAN-001",
                "transaction_date": _date(10),
                "product_name": "Standard Cable",
                "supplier_name": "Prime Cables",
                "quantity": 50,
                "unit_price": 40,
                "total_amount": 2000,
            }],
        )
        persist_sales(
            db_session,
            business.id,
            [{
                "invoice_number": "S-CLEAN-001",
                "transaction_date": _date(5),
                "product_name": "Standard Cable",
                "customer_name": "Alpha Traders",
                "quantity": 20,
                "unit_price": 80,
                "total_amount": 1600,
                "cost_price": 40,
            }],
        )

    elif scenario_id == "margin_supplier_pressure":
        persist_purchases(
            db_session,
            business.id,
            [
                {
                    "invoice_number": "P-HIST-001",
                    "transaction_date": _date(50),
                    "product_name": "HDMI Cable 2M",
                    "supplier_name": "Prime Cables",
                    "quantity": 10,
                    "unit_price": 40,
                    "total_amount": 400,
                },
                {
                    "invoice_number": "P-CUR-001",
                    "transaction_date": _date(10),
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
            [{
                "invoice_number": "S-CUR-001",
                "transaction_date": _date(5),
                "product_name": "HDMI Cable 2M",
                "customer_name": "Alpha Traders",
                "quantity": 60,
                "unit_price": 75,
                "total_amount": 4500,
                "cost_price": 80,
            }],
        )

    elif scenario_id == "working_capital_pressure":
        persist_purchases(
            db_session,
            business.id,
            [{
                "invoice_number": "P-WC-001",
                "transaction_date": _date(75),
                "product_name": "HDMI Cable 2M",
                "supplier_name": "Prime Cables",
                "quantity": 20,
                "unit_price": 60,
                "total_amount": 1200,
                "due_date": _date(75),
                "paid_amount": 0,
            }],
        )
        persist_sales(
            db_session,
            business.id,
            [{
                "invoice_number": "S-WC-001",
                "transaction_date": _date(75),
                "product_name": "HDMI Cable 2M",
                "customer_name": "Alpha Traders",
                "quantity": 20,
                "unit_price": 100,
                "total_amount": 2000,
                "due_date": _date(75),
                "paid_amount": 0,
                "cost_price": 60,
            }],
        )

    else:
        raise AssertionError(f"Unknown scenario: {scenario_id}")

    db_session.commit()
    return business


def test_sme_scenario_matrix_runs_through_real_business_context(db_session):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for scenario in fixture["scenarios"]:
        business = _seed_scenario(db_session, scenario["id"])
        context = build_business_context(db_session, business.id, date.today())

        signal_codes = {signal.code for signal in context.signals}
        situation_codes = {situation.code for situation in context.situations}
        action_codes = {action.code for action in context.decision_actions}
        root_cause_codes = {
            cause.code
            for analysis in context.analyses
            for cause in analysis.root_causes
        }

        for expected in scenario.get("expected_signals", []):
            assert expected in signal_codes, (
                f"{scenario['id']}: missing expected signal {expected}; "
                f"actual={sorted(signal_codes)}"
            )

        assert situation_codes == set(scenario.get("expected_situations", [])), (
            f"{scenario['id']}: unexpected situations; "
            f"expected={scenario.get('expected_situations', [])}, "
            f"actual={sorted(situation_codes)}"
        )

        assert action_codes == set(scenario.get("expected_actions", [])), (
            f"{scenario['id']}: unexpected decision actions; "
            f"expected={scenario.get('expected_actions', [])}, "
            f"actual={sorted(action_codes)}"
        )

        assert root_cause_codes == set(scenario.get("expected_root_causes", [])), (
            f"{scenario['id']}: unexpected root causes; "
            f"expected={scenario.get('expected_root_causes', [])}, "
            f"actual={sorted(root_cause_codes)}"
        )

        if scenario["id"] == "clean":
            assert context.integrity["status"] == "reconciled"
            assert not context.situations
            assert not context.decision_actions
        else:
            assert context.integrity["status"] == "reconciled"
            assert context.state is not None
            assert context.state.metadata["cash_position"] is None
