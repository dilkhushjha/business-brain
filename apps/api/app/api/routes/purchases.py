from datetime import date, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.models import PurchaseModel, PurchaseLineModel, SupplierModel, ProductModel
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
