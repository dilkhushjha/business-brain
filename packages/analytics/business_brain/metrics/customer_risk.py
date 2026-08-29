from __future__ import annotations
from datetime import date, timedelta
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import CustomerModel, SaleModel


def inactive_customers(db: Session, business_id: UUID, inactive_days: int = 45, limit: int = 10) -> list[dict[str, Any]]:
    cutoff = date.today() - timedelta(days=inactive_days)
    rows = db.execute(
        select(CustomerModel.name, func.max(SaleModel.transaction_date).label("last_order"), func.sum(SaleModel.total_amount).label("lifetime_revenue"))
        .join(SaleModel, SaleModel.customer_id == CustomerModel.id)
        .where(SaleModel.business_id == business_id)
        .group_by(CustomerModel.id, CustomerModel.name)
        .having(func.max(SaleModel.transaction_date) < cutoff)
        .order_by(func.max(SaleModel.transaction_date).desc())
        .limit(limit)
    ).all()
    today = date.today()
    return [{"name": name, "last_order": last_order.isoformat() if last_order else None,
             "inactive_days": (today - last_order).days if last_order else None,
             "lifetime_revenue": float(revenue or 0)} for name, last_order, revenue in rows]
