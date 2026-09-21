from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import (
    InventoryMovementModel,
    ProductModel,
    PurchaseLineModel,
    PurchaseModel,
    SaleLineModel,
    SaleModel,
)


def _window(days: int) -> tuple[date, date]:
    end = date.today()
    return end - timedelta(days=max(1, days) - 1), end


def _expected_purchase(db: Session, business_id: UUID, start: date, end: date):
    rows = db.execute(
        select(
            PurchaseModel.invoice_number,
            ProductModel.id,
            ProductModel.name,
            func.coalesce(func.sum(PurchaseLineModel.quantity), 0),
        )
        .join(PurchaseLineModel, PurchaseLineModel.purchase_id == PurchaseModel.id)
        .join(ProductModel, ProductModel.id == PurchaseLineModel.product_id)
        .where(
            PurchaseModel.business_id == business_id,
            PurchaseModel.transaction_date.between(start, end),
        )
        .group_by(PurchaseModel.invoice_number, ProductModel.id, ProductModel.name)
    ).all()
    return {(r[0], r[1]): {"product": r[2], "quantity": Decimal(str(r[3]))} for r in rows}


def _expected_sale(db: Session, business_id: UUID, start: date, end: date):
    rows = db.execute(
        select(
            SaleModel.invoice_number,
            ProductModel.id,
            ProductModel.name,
            func.coalesce(func.sum(SaleLineModel.quantity), 0),
        )
        .join(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
        .join(ProductModel, ProductModel.id == SaleLineModel.product_id)
        .where(
            SaleModel.business_id == business_id,
            SaleModel.transaction_date.between(start, end),
        )
        .group_by(SaleModel.invoice_number, ProductModel.id, ProductModel.name)
    ).all()
    return {(r[0], r[1]): {"product": r[2], "quantity": Decimal(str(r[3]))} for r in rows}


def _actual_movements(
    db: Session,
    business_id: UUID,
    movement_type: str,
    start: date,
    end: date,
):
    rows = db.execute(
        select(
            InventoryMovementModel.reference,
            InventoryMovementModel.product_id,
            ProductModel.name,
            func.coalesce(func.sum(InventoryMovementModel.quantity), 0),
        )
        .join(ProductModel, ProductModel.id == InventoryMovementModel.product_id)
        .where(
            InventoryMovementModel.business_id == business_id,
            InventoryMovementModel.movement_type == movement_type,
            InventoryMovementModel.movement_date.between(start, end),
        )
        .group_by(
            InventoryMovementModel.reference,
            InventoryMovementModel.product_id,
            ProductModel.name,
        )
    ).all()
    return {(r[0], r[1]): {"product": r[2], "quantity": Decimal(str(r[3]))} for r in rows}


def _compare(expected, actual, movement_type: str):
    mismatches = []
    for key in sorted(set(expected) | set(actual), key=lambda item: (str(item[0]), str(item[1]))):
        exp = expected.get(key)
        act = actual.get(key)
        expected_qty = exp["quantity"] if exp else Decimal("0")
        actual_qty = act["quantity"] if act else Decimal("0")
        if expected_qty != actual_qty:
            mismatches.append({
                "movement_type": movement_type,
                "invoice_number": key[0],
                "product": (exp or act)["product"],
                "expected_quantity": float(expected_qty),
                "actual_quantity": float(actual_qty),
                "difference": float(actual_qty - expected_qty),
            })
    return mismatches


def audit_inventory_integrity(
    db: Session,
    business_id: UUID,
    days: int = 3650,
    limit: int = 50,
) -> dict:
    """Audit canonical documents against their source-owned inventory ledger.

    This is deliberately read-only. Missing or inconsistent data is surfaced
    as an exception rather than inferred or silently repaired.
    """
    start, end = _window(days)
    limit = max(1, min(limit, 200))

    expected_purchase = _expected_purchase(db, business_id, start, end)
    expected_sale = _expected_sale(db, business_id, start, end)
    actual_purchase = _actual_movements(db, business_id, "purchase", start, end)
    actual_sale = _actual_movements(db, business_id, "sale", start, end)

    purchase_mismatches = _compare(expected_purchase, actual_purchase, "purchase")
    sale_mismatches = _compare(expected_sale, actual_sale, "sale")

    purchase_refs = {key[0] for key in expected_purchase}
    sale_refs = {key[0] for key in expected_sale}
    orphan_rows = db.execute(
        select(
            InventoryMovementModel.reference,
            InventoryMovementModel.movement_type,
            ProductModel.name,
            InventoryMovementModel.quantity,
        )
        .join(ProductModel, ProductModel.id == InventoryMovementModel.product_id)
        .where(
            InventoryMovementModel.business_id == business_id,
            InventoryMovementModel.movement_type.in_(["purchase", "sale"]),
            InventoryMovementModel.movement_date.between(start, end),
            InventoryMovementModel.reference.is_not(None),
        )
    ).all()

    orphans = []
    for reference, movement_type, product, quantity in orphan_rows:
        valid_refs = purchase_refs if movement_type == "purchase" else sale_refs
        if reference not in valid_refs:
            orphans.append({
                "movement_type": movement_type,
                "invoice_number": reference,
                "product": product,
                "quantity": float(quantity),
            })

    balances = db.execute(
        select(
            ProductModel.name,
            func.coalesce(
                func.sum(
                    InventoryMovementModel.quantity
                    * case(
                        (InventoryMovementModel.movement_type.in_(["purchase", "return_in"]), 1),
                        else_=-1,
                    )
                ),
                0,
            ),
        )
        .join(ProductModel, ProductModel.id == InventoryMovementModel.product_id)
        .where(
            InventoryMovementModel.business_id == business_id,
            InventoryMovementModel.movement_date <= end,
        )
        .group_by(ProductModel.id, ProductModel.name)
    ).all()

    negative_balances = [
        {"product": name, "movement_balance": float(quantity)}
        for name, quantity in balances
        if Decimal(str(quantity)) < 0
    ]
    negative_balances.sort(key=lambda item: item["movement_balance"])

    issue_count = (
        len(purchase_mismatches)
        + len(sale_mismatches)
        + len(orphans)
        + len(negative_balances)
    )

    return {
        "status": "attention_required" if issue_count else "reconciled",
        "period_days": days,
        "purchase_line_mismatches": purchase_mismatches[:limit],
        "sale_line_mismatches": sale_mismatches[:limit],
        "inventory_movement_orphans": orphans[:limit],
        "negative_movement_balances": negative_balances[:limit],
        "summary": {
            "purchase_line_mismatch_count": len(purchase_mismatches),
            "sale_line_mismatch_count": len(sale_mismatches),
            "orphan_movement_count": len(orphans),
            "negative_balance_count": len(negative_balances),
            "issue_count": issue_count,
        },
    }
