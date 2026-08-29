from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import CustomerModel, ProductModel, SaleLineModel, SaleModel


def top_products(db: Session, business_id: UUID, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    end = date.today(); start = end - timedelta(days=max(1, days) - 1)
    rows = db.execute(
        select(ProductModel.name, func.sum(SaleLineModel.quantity).label("quantity"),
               func.sum(SaleLineModel.quantity * SaleLineModel.unit_price).label("revenue"))
        .join(SaleLineModel, SaleLineModel.product_id == ProductModel.id)
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
        .where(SaleModel.business_id == business_id, SaleModel.transaction_date.between(start, end))
        .group_by(ProductModel.id, ProductModel.name)
        .order_by(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price).desc())
        .limit(limit)
    ).all()
    return [{"name": name, "quantity": float(quantity or 0), "revenue": float(revenue or 0)}
            for name, quantity, revenue in rows]


def top_customers(db: Session, business_id: UUID, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    end = date.today(); start = end - timedelta(days=max(1, days) - 1)
    rows = db.execute(
        select(CustomerModel.name, func.count(SaleModel.id).label("orders"),
               func.sum(SaleModel.total_amount).label("revenue"))
        .join(SaleModel, SaleModel.customer_id == CustomerModel.id)
        .where(SaleModel.business_id == business_id, SaleModel.transaction_date.between(start, end))
        .group_by(CustomerModel.id, CustomerModel.name)
        .order_by(func.sum(SaleModel.total_amount).desc())
        .limit(limit)
    ).all()
    return [{"name": name, "orders": int(orders or 0), "revenue": float(revenue or 0)}
            for name, orders, revenue in rows]
