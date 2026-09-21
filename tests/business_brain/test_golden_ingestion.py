from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select

from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import (
    InventoryMovementModel,
    ProductModel,
    PurchaseModel,
    SaleModel,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "golden_sme_distribution.json"


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


def test_golden_dataset_persists_into_canonical_sales_purchases_and_inventory(db_session):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    business = __import__("tests.conftest", fromlist=["Seeder"]).Seeder(db_session).business(
        name=data["business"]["name"], industry=data["business"]["industry"]
    )

    sales, purchases = _rows(data)
    sale_result = persist_sales(db_session, business.id, sales)
    purchase_result = persist_purchases(db_session, business.id, purchases)
    db_session.commit()

    assert sale_result == {"created": 3, "reconciled": 0}
    assert purchase_result == {"created": 3, "reconciled": 0}
    assert db_session.scalar(select(func.count()).select_from(SaleModel)) == 3
    assert db_session.scalar(select(func.count()).select_from(PurchaseModel)) == 3

    products = {
        p.name: p.id
        for p in db_session.scalars(
            select(ProductModel).where(ProductModel.business_id == business.id)
        )
    }
    movements = db_session.scalars(
        select(InventoryMovementModel).where(
            InventoryMovementModel.business_id == business.id
        )
    ).all()

    for product_name, expected_units in data["expected"]["inventory_units"].items():
        balance = sum(
            (m.quantity if m.movement_type == "purchase" else -m.quantity)
            for m in movements
            if m.product_id == products[product_name]
        )
        assert balance == Decimal(str(expected_units))


def test_golden_dataset_reimport_reconciles_instead_of_duplicating(db_session):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    seeder = __import__("tests.conftest", fromlist=["Seeder"]).Seeder(db_session)
    business = seeder.business(name=data["business"]["name"], industry=data["business"]["industry"])

    sales, purchases = _rows(data)
    persist_sales(db_session, business.id, sales)
    persist_purchases(db_session, business.id, purchases)
    db_session.commit()

    changed_sale = dict(sales[0], quantity=70, total_amount=Decimal("5250"))
    changed_purchase = dict(purchases[0], quantity=160, total_amount=Decimal("6400"))

    assert persist_sales(db_session, business.id, [changed_sale]) == {"created": 0, "reconciled": 1}
    assert persist_purchases(db_session, business.id, [changed_purchase]) == {"created": 0, "reconciled": 1}
    db_session.commit()

    assert db_session.scalar(select(func.count()).select_from(SaleModel)) == 3
    assert db_session.scalar(select(func.count()).select_from(PurchaseModel)) == 3

    product = db_session.scalar(
        select(ProductModel).where(
            ProductModel.business_id == business.id,
            ProductModel.name == "HDMI Cable 2M",
        )
    )
    movements = db_session.scalars(
        select(InventoryMovementModel).where(
            InventoryMovementModel.business_id == business.id,
            InventoryMovementModel.product_id == product.id,
        )
    ).all()

    purchase_units = sum(m.quantity for m in movements if m.movement_type == "purchase")
    sale_units = sum(m.quantity for m in movements if m.movement_type == "sale")
    assert purchase_units == Decimal("160")
    assert sale_units == Decimal("70")
