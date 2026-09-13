from decimal import Decimal

from sqlalchemy import select

from packages.data.business_brain.ingestion.inventory_repository import persist_inventory_snapshots
from packages.shared.database.models import InventorySnapshotModel, ProductModel


def test_persist_inventory_snapshots_creates_snapshot(db_session, seeder):
    business = seeder.business()
    rows = [{
        "transaction_date": "31-08-2026", "product_name": "LED Bulb 9W",
        "closing_qty": "150", "closing_value": "9000",
    }]

    created = persist_inventory_snapshots(db_session, business.id, rows)
    db_session.commit()

    assert created == 1
    snapshot = db_session.execute(select(InventorySnapshotModel).where(InventorySnapshotModel.business_id == business.id)).scalar_one()
    assert snapshot.quantity == Decimal("150")
    assert snapshot.value == Decimal("9000")
    product = db_session.execute(select(ProductModel).where(ProductModel.business_id == business.id)).scalar_one()
    assert product.name == "LED Bulb 9W"


def test_persist_inventory_snapshots_updates_same_date_snapshot(db_session, seeder):
    """Re-importing the same as-on-date's Stock Summary (a corrected
    export) should update the existing snapshot, not duplicate it --
    the (business, product, date) unique constraint is the natural key."""
    business = seeder.business()
    first_pass = [{
        "transaction_date": "31-08-2026", "product_name": "LED Bulb 9W",
        "closing_qty": "150", "closing_value": "9000",
    }]
    persist_inventory_snapshots(db_session, business.id, first_pass)
    db_session.commit()

    second_pass = [{
        "transaction_date": "31-08-2026", "product_name": "LED Bulb 9W",
        "closing_qty": "140", "closing_value": "8400",
    }]
    created = persist_inventory_snapshots(db_session, business.id, second_pass)
    db_session.commit()

    assert created == 0
    snapshots = db_session.execute(select(InventorySnapshotModel).where(InventorySnapshotModel.business_id == business.id)).scalars().all()
    assert len(snapshots) == 1
    assert snapshots[0].quantity == Decimal("140")


def test_persist_inventory_snapshots_creates_separate_rows_for_different_dates(db_session, seeder):
    business = seeder.business()
    rows = [
        {"transaction_date": "31-07-2026", "product_name": "LED Bulb 9W", "closing_qty": "200", "closing_value": "12000"},
        {"transaction_date": "31-08-2026", "product_name": "LED Bulb 9W", "closing_qty": "150", "closing_value": "9000"},
    ]

    created = persist_inventory_snapshots(db_session, business.id, rows)
    db_session.commit()

    assert created == 2
    snapshots = db_session.execute(select(InventorySnapshotModel).where(InventorySnapshotModel.business_id == business.id)).scalars().all()
    assert len(snapshots) == 2


def test_persist_inventory_snapshots_reuses_existing_product(db_session, seeder):
    business = seeder.business()
    seeder.product(business.id, "LED Bulb 9W")

    rows = [{
        "transaction_date": "31-08-2026", "product_name": "LED Bulb 9W",
        "closing_qty": "150", "closing_value": "9000",
    }]
    persist_inventory_snapshots(db_session, business.id, rows)
    db_session.commit()

    products = db_session.execute(select(ProductModel).where(ProductModel.business_id == business.id)).scalars().all()
    assert len(products) == 1


def test_persist_inventory_snapshots_allows_zero_stock(db_session, seeder):
    """A stocked-out item is a real, important snapshot -- zero units on
    hand should persist correctly, not be treated as missing data."""
    business = seeder.business()
    rows = [{
        "transaction_date": "31-08-2026", "product_name": "Out Of Stock Item",
        "closing_qty": "0", "closing_value": "0",
    }]

    created = persist_inventory_snapshots(db_session, business.id, rows)
    db_session.commit()

    assert created == 1
    snapshot = db_session.execute(select(InventorySnapshotModel).where(InventorySnapshotModel.business_id == business.id)).scalar_one()
    assert snapshot.quantity == Decimal("0")
