from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import PurchaseModel, SupplierModel

def supplier_spend_risk(db: Session, business_id: UUID, days: int = 90, as_of: date | None = None) -> dict:
    end=as_of or date.today(); start=end-timedelta(days=days-1); prev_start=start-timedelta(days=days)
    rows=db.execute(select(SupplierModel.name, func.coalesce(func.sum(PurchaseModel.total_amount),0))
        .join(PurchaseModel, PurchaseModel.supplier_id==SupplierModel.id)
        .where(PurchaseModel.business_id==business_id,PurchaseModel.transaction_date.between(start,end))
        .group_by(SupplierModel.id,SupplierModel.name).order_by(func.sum(PurchaseModel.total_amount).desc())).all()
    total=sum(float(x[1]) for x in rows)
    top=rows[0] if rows else None
    risks=[]
    for name,amount in rows:
        current=float(amount)
        previous=float(db.scalar(select(func.coalesce(func.sum(PurchaseModel.total_amount),0)).where(
            PurchaseModel.business_id==business_id,PurchaseModel.supplier_id==select(SupplierModel.id).where(SupplierModel.name==name).scalar_subquery(),
            PurchaseModel.transaction_date.between(prev_start,start-timedelta(days=1)))) or 0)
        change=(current-previous)/previous*100 if previous else None
        if change is not None and change>=25:
            risks.append({"supplier":name,"current_spend":current,"previous_spend":previous,"change_pct":round(change,2)})
    return {"total_spend":round(total,2),"top_supplier":top[0] if top else None,
            "top_share_pct":round(float(top[1])/total*100,2) if top and total else 0,"spend_spikes":risks}


def purchase_integrity_summary(db: Session, business_id: UUID, days: int = 3650) -> dict:
    """Summarize purchase-side data quality without guessing missing values."""
    end = date.today()
    start = end - timedelta(days=max(1, days) - 1)
    total = float(db.scalar(select(func.coalesce(func.sum(PurchaseModel.total_amount), 0)).where(
        PurchaseModel.business_id == business_id,
        PurchaseModel.transaction_date.between(start, end),
    )) or 0)
    invoice_count = int(db.scalar(select(func.count(PurchaseModel.id)).where(
        PurchaseModel.business_id == business_id,
        PurchaseModel.transaction_date.between(start, end),
    )) or 0)
    missing_supplier = int(db.scalar(select(func.count(PurchaseModel.id)).where(
        PurchaseModel.business_id == business_id,
        PurchaseModel.supplier_id.is_(None),
        PurchaseModel.transaction_date.between(start, end),
    )) or 0)
    return {
        "period_days": days,
        "purchase_invoice_count": invoice_count,
        "purchase_total": round(total, 2),
        "missing_supplier_count": missing_supplier,
        "status": "attention_required" if missing_supplier else "reconciled",
    }
