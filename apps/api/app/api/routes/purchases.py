from datetime import date, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.models import PaymentModel, PurchaseModel, PurchaseLineModel, SupplierModel, ProductModel
from packages.shared.database.session import get_db

router = APIRouter(prefix="/purchases", tags=["purchases"])

def _start(days: int) -> date:
    return date.today() - timedelta(days=max(1, days) - 1)

@router.get("/{business_id}/summary")
def purchase_summary(business_id: UUID, days: int = 30, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    start = _start(days)
    row = db.execute(select(
        func.coalesce(func.sum(PurchaseModel.total_amount), 0),
        func.count(PurchaseModel.id),
        func.coalesce(func.sum(PurchaseModel.total_amount - PurchaseModel.paid_amount), 0),
    ).where(PurchaseModel.business_id == business_id, PurchaseModel.transaction_date >= start)).one()
    return {"total_amount": float(row[0]), "invoice_count": int(row[1]), "outstanding": float(row[2]), "days": days}

@router.get("/{business_id}/suppliers")
def purchase_suppliers(business_id: UUID, days: int = 30, limit: int = 5, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    start = _start(days)
    rows = db.execute(select(
        SupplierModel.name, func.count(PurchaseModel.id),
        func.coalesce(func.sum(PurchaseModel.total_amount), 0),
        func.coalesce(func.sum(PurchaseModel.total_amount - PurchaseModel.paid_amount), 0),
    ).join(PurchaseModel, PurchaseModel.supplier_id == SupplierModel.id)
    .where(PurchaseModel.business_id == business_id, PurchaseModel.transaction_date >= start)
    .group_by(SupplierModel.id, SupplierModel.name)
    .order_by(func.sum(PurchaseModel.total_amount).desc()).limit(max(1, min(limit, 50)))).all()
    return [{"name": r[0], "purchases": int(r[1]), "amount": float(r[2]), "paid": float(r[2] - r[3]), "outstanding": float(r[3])} for r in rows]

@router.get("/{business_id}/products")
def purchase_products(business_id: UUID, days: int = 30, limit: int = 5, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    start = _start(days)
    rows = db.execute(select(
        ProductModel.name,
        func.coalesce(func.sum(PurchaseLineModel.quantity), 0),
        func.coalesce(func.sum(PurchaseLineModel.net_amount), 0),
        func.coalesce(func.sum(PurchaseLineModel.net_amount) / func.nullif(func.sum(PurchaseLineModel.quantity), 0), 0),
    ).join(PurchaseLineModel, PurchaseLineModel.product_id == ProductModel.id)
    .join(PurchaseModel, PurchaseModel.id == PurchaseLineModel.purchase_id)
    .where(PurchaseModel.business_id == business_id, PurchaseModel.transaction_date >= start)
    .group_by(ProductModel.id, ProductModel.name)
    .order_by(func.sum(PurchaseLineModel.net_amount).desc()).limit(max(1, min(limit, 50)))).all()
    return [{"name": r[0], "quantity": float(r[1]), "amount": float(r[2]), "unit_cost": float(r[3])} for r in rows]


@router.get("/{business_id}/supplier-intelligence")
def supplier_intelligence(
    business_id: UUID,
    days: int = 90,
    limit: int = 10,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Supplier concentration, spend trend and cost movement signals."""
    from datetime import date, timedelta
    end = date.today()
    start = end - timedelta(days=max(1, days) - 1)
    previous_start = start - timedelta(days=max(1, days))

    current_rows = db.execute(
        select(
            SupplierModel.id,
            SupplierModel.name,
            func.count(PurchaseModel.id),
            func.coalesce(func.sum(PurchaseModel.total_amount), 0),
            func.coalesce(func.sum(PurchaseModel.total_amount - PurchaseModel.paid_amount), 0),
        )
        .join(PurchaseModel, PurchaseModel.supplier_id == SupplierModel.id)
        .where(PurchaseModel.business_id == business_id, PurchaseModel.transaction_date.between(start, end))
        .group_by(SupplierModel.id, SupplierModel.name)
        .order_by(func.sum(PurchaseModel.total_amount).desc())
        .limit(max(1, min(limit, 50)))
    ).all()

    total_spend = sum(float(r[3]) for r in current_rows)
    suppliers = []
    for supplier_id, name, invoices, spend, outstanding in current_rows:
        previous = db.scalar(
            select(func.coalesce(func.sum(PurchaseModel.total_amount), 0))
            .where(
                PurchaseModel.business_id == business_id,
                PurchaseModel.supplier_id == supplier_id,
                PurchaseModel.transaction_date.between(previous_start, start - timedelta(days=1)),
            )
        ) or 0
        share = float(spend) / total_spend * 100 if total_spend else 0
        previous = float(previous)
        change = ((float(spend) - previous) / previous * 100) if previous else None
        suppliers.append({
            "name": name,
            "invoice_count": int(invoices),
            "spend": float(spend),
            "outstanding": float(outstanding),
            "share_pct": round(share, 2),
            "previous_spend": previous,
            "change_pct": round(change, 2) if change is not None else None,
        })

    concentration = sum(x["share_pct"] for x in suppliers)
    return {
        "days": days,
        "total_spend": round(total_spend, 2),
        "supplier_count": len(suppliers),
        "top_supplier_share_pct": suppliers[0]["share_pct"] if suppliers else 0,
        "top_supplier": suppliers[0]["name"] if suppliers else None,
        "top_suppliers_share_pct": round(concentration, 2),
        "suppliers": suppliers,
    }


@router.get("/{business_id}/supplier-cost-changes")
def supplier_cost_changes(
    business_id: UUID,
    days: int = 90,
    threshold_pct: float = 5,
    limit: int = 10,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Detect meaningful product unit-cost increases by supplier."""
    from datetime import date, timedelta
    end = date.today()
    start = end - timedelta(days=max(1, days) - 1)
    midpoint = start + timedelta(days=max(1, days) // 2)

    rows = db.execute(
        select(
            SupplierModel.name,
            ProductModel.name,
            func.sum(PurchaseLineModel.quantity),
            func.sum(PurchaseLineModel.net_amount),
            PurchaseModel.transaction_date,
        )
        .join(PurchaseModel, PurchaseModel.supplier_id == SupplierModel.id)
        .join(PurchaseLineModel, PurchaseLineModel.purchase_id == PurchaseModel.id)
        .join(ProductModel, ProductModel.id == PurchaseLineModel.product_id)
        .where(
            PurchaseModel.business_id == business_id,
            PurchaseModel.transaction_date.between(start, end),
        )
        .group_by(SupplierModel.name, ProductModel.name, PurchaseModel.transaction_date)
        .order_by(PurchaseModel.transaction_date)
    ).all()

    grouped = {}
    for supplier, product, qty, amount, tx_date in rows:
        key = (supplier, product)
        period = "early" if tx_date < midpoint else "late"
        item = grouped.setdefault(key, {"early_qty": 0, "early_amount": 0, "late_qty": 0, "late_amount": 0})
        item[f"{period}_qty"] += float(qty or 0)
        item[f"{period}_amount"] += float(amount or 0)

    changes = []
    for (supplier, product), x in grouped.items():
        if x["early_qty"] <= 0 or x["late_qty"] <= 0:
            continue
        old_cost = x["early_amount"] / x["early_qty"]
        new_cost = x["late_amount"] / x["late_qty"]
        change = (new_cost - old_cost) / old_cost * 100 if old_cost else 0
        if change >= threshold_pct:
            changes.append({
                "supplier": supplier,
                "product": product,
                "previous_unit_cost": round(old_cost, 2),
                "current_unit_cost": round(new_cost, 2),
                "change_pct": round(change, 2),
            })

    return sorted(changes, key=lambda x: x["change_pct"], reverse=True)[:max(1, min(limit, 50))]


@router.get("/{business_id}/financial-linkage")
def purchase_financial_linkage(
    business_id: UUID,
    days: int = 90,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Connect purchase liabilities with supplier payments and cash outflow."""
    end = date.today()
    start = _start(days)

    purchase_total = db.scalar(
        select(func.coalesce(func.sum(PurchaseModel.total_amount), 0)).where(
            PurchaseModel.business_id == business_id,
            PurchaseModel.transaction_date.between(start, end),
        )
    ) or 0
    purchase_paid = db.scalar(
        select(func.coalesce(func.sum(PurchaseModel.paid_amount), 0)).where(
            PurchaseModel.business_id == business_id,
            PurchaseModel.transaction_date.between(start, end),
        )
    ) or 0
    purchase_outstanding = db.scalar(
        select(func.coalesce(func.sum(PurchaseModel.total_amount - PurchaseModel.paid_amount), 0)).where(
            PurchaseModel.business_id == business_id,
            PurchaseModel.transaction_date.between(start, end),
        )
    ) or 0

    supplier_payments = db.scalar(
        select(func.coalesce(func.sum(PaymentModel.amount), 0)).where(
            PaymentModel.business_id == business_id,
            PaymentModel.supplier_id.is_not(None),
            PaymentModel.direction == "out",
            PaymentModel.payment_date.between(start, end),
        )
    ) or 0

    return {
        "days": days,
        "purchase_total": float(purchase_total),
        "purchase_paid_on_documents": float(purchase_paid),
        "purchase_outstanding": float(purchase_outstanding),
        "supplier_cash_outflow": float(supplier_payments),
        "payment_coverage_pct": round(float(supplier_payments / purchase_total * 100), 2) if purchase_total else 0,
    }
