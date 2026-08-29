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


def customer_concentration(db: Session, business_id: UUID, top_n: int = 5) -> dict[str, Any]:
    rows = db.execute(select(CustomerModel.name, func.sum(SaleModel.total_amount).label("revenue")).join(SaleModel, SaleModel.customer_id == CustomerModel.id).where(SaleModel.business_id == business_id).group_by(CustomerModel.id, CustomerModel.name).order_by(func.sum(SaleModel.total_amount).desc())).all()
    total = sum(float(r.revenue or 0) for r in rows)
    top = [{"name": r.name, "revenue": float(r.revenue or 0), "share_pct": round(float(r.revenue or 0)/total*100,2) if total else 0} for r in rows[:top_n]]
    top_share = round(sum(x["share_pct"] for x in top),2)
    level = "high" if top_share >= 60 or (top and top[0]["share_pct"] >= 35) else "medium" if top_share >= 40 or (top and top[0]["share_pct"] >= 20) else "low"
    return {"total_revenue": total, "top_customers": top, "top_n": top_n, "top_share_pct": top_share, "risk": level}
