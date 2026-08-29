from __future__ import annotations
from datetime import date, timedelta
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import CustomerModel, SaleModel


def inactive_customers(db: Session, business_id: UUID, inactive_days: int = 45, limit: int = 10) -> list[dict[str, Any]]:
    cutoff = date.today() - timedelta(days=inactive_days)
    rows = db.execute(select(CustomerModel.name, func.max(SaleModel.transaction_date).label("last_order"), func.sum(SaleModel.total_amount).label("lifetime_revenue")).join(SaleModel, SaleModel.customer_id == CustomerModel.id).where(SaleModel.business_id == business_id).group_by(CustomerModel.id, CustomerModel.name).having(func.max(SaleModel.transaction_date) < cutoff).order_by(func.max(SaleModel.transaction_date).desc()).limit(limit)).all()
    today = date.today()
    return [{"name": name, "last_order": last.isoformat() if last else None, "inactive_days": (today-last).days if last else None, "lifetime_revenue": float(revenue or 0)} for name,last,revenue in rows]


def declining_customers(db: Session, business_id: UUID, days: int = 30, threshold: float = 25, limit: int = 10) -> list[dict[str, Any]]:
    end = date.today(); cur_start = end - timedelta(days=days-1); prev_end = cur_start - timedelta(days=1); prev_start = prev_end - timedelta(days=days-1)
    rows = db.execute(select(CustomerModel.id, CustomerModel.name).join(SaleModel, SaleModel.customer_id == CustomerModel.id).where(SaleModel.business_id == business_id).group_by(CustomerModel.id, CustomerModel.name)).all()
    result=[]
    for cid,name in rows:
        cur=float(db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount),0)).where(SaleModel.business_id==business_id,SaleModel.customer_id==cid,SaleModel.transaction_date.between(cur_start,end))) or 0)
        prev=float(db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount),0)).where(SaleModel.business_id==business_id,SaleModel.customer_id==cid,SaleModel.transaction_date.between(prev_start,prev_end))) or 0)
        if prev and (prev-cur)/prev*100 >= threshold:
            result.append({"name":name,"current_revenue":cur,"previous_revenue":prev,"change_pct":round((cur-prev)/prev*100,2),"severity":"high" if (prev-cur)/prev*100>=50 else "medium"})
    return sorted(result,key=lambda x:x["change_pct"])[:limit]
