from __future__ import annotations
from datetime import date, timedelta
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import CustomerModel, SaleModel


def customer_concentration(db: Session, business_id: UUID, days: int = 90, limit: int = 5) -> dict[str, Any]:
    end = date.today(); start = end - timedelta(days=days - 1)
    total = float(db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount), 0)).where(SaleModel.business_id == business_id, SaleModel.transaction_date.between(start, end))) or 0)
    rows = db.execute(select(CustomerModel.name, func.sum(SaleModel.total_amount).label("revenue")).join(SaleModel, SaleModel.customer_id == CustomerModel.id).where(SaleModel.business_id == business_id, SaleModel.transaction_date.between(start, end)).group_by(CustomerModel.id, CustomerModel.name).order_by(func.sum(SaleModel.total_amount).desc()).limit(limit)).all()
    top = [{"name": name, "revenue": float(revenue or 0), "share_pct": round((float(revenue or 0) / total * 100), 2) if total else 0} for name, revenue in rows]
    top_share = round(sum(x["share_pct"] for x in top), 2)
    return {"period_days": days, "total_revenue": total, "top_customers": top, "top_customer_share_pct": top[0]["share_pct"] if top else 0, "top_5_share_pct": top_share, "risk": "high" if top_share >= 60 else "medium" if top_share >= 40 else "low"}
