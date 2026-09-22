from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select

from packages.analytics.business_brain.business_integrity import audit_business_integrity
from packages.analytics.business_brain.context.builder import build_business_context
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import (
    BusinessModel,
    InventoryMovementModel,
    PurchaseModel,
    SaleModel,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "golden_sme_distribution.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _create_business(db, data: dict) -> BusinessModel:
    business = BusinessModel(
        id=uuid4(),
        name=data["business"]["name"],
        industry=data["business"]["industry"],
    )
    db.add(business)
    db.commit()
    return business


def _rows(data: dict) -> tuple[list[dict], list[dict]]:
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
    return sales, purchases


def test_golden_path_from_import_to_business_brain(db_session):
    data = _load_fixture()
    business = _create_business(db_session, data)
    sales, purchases = _rows(data)

    # 1. Raw business data enters the canonical repositories.
    sales_result = persist_sales(db_session, business.id, sales)
    purchase_result = persist_purchases(db_session, business.id, purchases)
    db_session.commit()

    assert sales_result == {"created": 3, "reconciled": 0}
    assert purchase_result == {"created": 3, "reconciled": 0}

    # 2. Canonical documents and inventory movements agree with the source fixture.
    assert db_session.scalar(
        select(func.count()).select_from(SaleModel).where(SaleModel.business_id == business.id)
    ) == 3
    assert db_session.scalar(
        select(func.count()).select_from(PurchaseModel).where(PurchaseModel.business_id == business.id)
    ) == 3

    movements = db_session.scalars(
        select(InventoryMovementModel).where(
            InventoryMovementModel.business_id == business.id
        )
    ).all()

    inventory = {}
    for movement in movements:
        signed = movement.quantity if movement.movement_type == "purchase" else -movement.quantity
        inventory[movement.product_id] = inventory.get(movement.product_id, Decimal("0")) + signed
    assert sorted(inventory.values()) == [Decimal("60"), Decimal("90"), Decimal("120")]

    # 3. Integrity is clean before intelligence is allowed to reason over it.
    integrity = audit_business_integrity(db_session, business.id)
    assert integrity["status"] == "reconciled"
    assert integrity["issue_count"] == 0

    # 4. Business Brain turns the same canonical data into state/evidence/signals.
    context = build_business_context(db_session, business.id, date(2026, 9, 20))

    assert context.state is not None
    assert context.state.revenue == Decimal("12500")
    assert context.state.purchase_spend == Decimal("17500")
    assert context.state.metadata["cash_position"] is None
    assert context.evidence
    assert isinstance(context.signals, list)
    assert isinstance(context.situations, list)
    assert isinstance(context.analyses, list)
    assert isinstance(context.priorities, list)
    assert isinstance(context.decision_actions, list)
    assert isinstance(context.situation_history, list)

    # 5. A second import of changed documents reconciles the business instead
    # of creating duplicate canonical documents or stale inventory movements.
    changed_sale = dict(sales[0], quantity=70, total_amount=Decimal("5250"))
    changed_purchase = dict(purchases[0], quantity=160, total_amount=Decimal("6400"))

    assert persist_sales(db_session, business.id, [changed_sale]) == {
        "created": 0,
        "reconciled": 1,
    }
    assert persist_purchases(db_session, business.id, [changed_purchase]) == {
        "created": 0,
        "reconciled": 1,
    }
    db_session.commit()

    assert db_session.scalar(
        select(func.count()).select_from(SaleModel).where(SaleModel.business_id == business.id)
    ) == 3
    assert db_session.scalar(
        select(func.count()).select_from(PurchaseModel).where(PurchaseModel.business_id == business.id)
    ) == 3

    # Refreshing Business Brain after reconciliation must still produce a
    # coherent, evidence-backed context rather than stale pre-import state.
    refreshed = build_business_context(db_session, business.id, date(2026, 9, 20))
    assert refreshed.state.revenue == Decimal("13250")
    assert refreshed.state.purchase_spend == Decimal("17900")
    refreshed_integrity = audit_business_integrity(db_session, business.id)
    assert refreshed_integrity["status"] == "reconciled"
    assert refreshed_integrity["issue_count"] == 0
