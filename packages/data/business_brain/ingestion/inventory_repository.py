from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.canonicalize import canonicalize_inventory_snapshot_row
from packages.shared.database.models import InventorySnapshotModel, ProductModel


def _get_or_create_product(db: Session, business_id: UUID, name: str) -> ProductModel:
    stmt = select(ProductModel).where(ProductModel.business_id == business_id, ProductModel.name == name)
    product = db.execute(stmt).scalar_one_or_none()
    if product:
        return product
    product = ProductModel(business_id=business_id, name=name)
    db.add(product)
    db.flush()
    return product


def persist_inventory_snapshots(db: Session, business_id: UUID, rows: list[dict]) -> int:
    """Persist inventory snapshots. Unlike expenses, there's a real natural
    key here -- InventorySnapshotModel has a unique constraint on
    (business_id, product_id, snapshot_date), matching how a Stock Summary
    naturally works: one closing position per item per as-on date.
    Re-importing the same date's stock summary updates the existing
    snapshot (a corrected export) rather than erroring or duplicating.

    Returns the number of newly-created snapshots.
    """
    created = 0
    for raw in rows:
        row = canonicalize_inventory_snapshot_row(raw)
        product = _get_or_create_product(db, business_id, row["product_name"])

        existing = db.execute(
            select(InventorySnapshotModel).where(
                InventorySnapshotModel.business_id == business_id,
                InventorySnapshotModel.product_id == product.id,
                InventorySnapshotModel.snapshot_date == row["snapshot_date"],
            )
        ).scalar_one_or_none()

        if existing:
            existing.quantity = row["quantity"]
            existing.value = row["value"]
            continue

        db.add(InventorySnapshotModel(
            business_id=business_id,
            product_id=product.id,
            snapshot_date=row["snapshot_date"],
            quantity=row["quantity"],
            value=row["value"],
        ))
        created += 1

    return created
