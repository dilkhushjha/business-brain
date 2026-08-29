from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import ProductModel, SaleLineModel, SaleModel


def _money(value: Any) -> float:
    return float(value or 0)


def business_kpis(db: Session, business_id: UUID, as_of: date | None = None) -> dict[str, Any]:
    end = as_of or date.today()
    start = end - timedelta(days=29)
    previous_start = start - timedelta(days=30)
    previous_end = start - timedelta(days=1)

    def revenue(lo: date, hi: date) -> Decimal:
        return db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount), 0)).where(
            SaleModel.business_id == business_id,
            SaleModel.transaction_date.between(lo, hi),
        )) or Decimal("0")

    current = revenue(start, end)
    previous = revenue(previous_start, previous_end)
    growth = ((current - previous) / previous * 100) if previous else None
    orders = db.scalar(select(func.count(SaleModel.id)).where(
        SaleModel.business_id == business_id,
        SaleModel.transaction_date.between(start, end),
    )) or 0
    customers = db.scalar(select(func.count(func.distinct(SaleModel.customer_id))).where(
        SaleModel.business_id == business_id,
        SaleModel.transaction_date.between(start, end),
        SaleModel.customer_id.is_not(None),
    )) or 0
    top_products = db.execute(
        select(ProductModel.name, func.sum(SaleLineModel.quantity).label("quantity"),
               func.sum(SaleLineModel.quantity * SaleLineModel.unit_price).label("revenue"))
        .join(SaleLineModel, SaleLineModel.product_id == ProductModel.id)
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
        .where(SaleModel.business_id == business_id,
               SaleModel.transaction_date.between(start, end))
        .group_by(ProductModel.id, ProductModel.name)
        .order_by(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price).desc())
        .limit(5)
    ).all()
    return {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "revenue": _money(current),
        "previous_revenue": _money(previous),
        "revenue_growth_pct": round(float(growth), 2) if growth is not None else None,
        "orders": orders,
        "average_order_value": round(_money(current) / orders, 2) if orders else 0,
        "active_customers": customers,
        "top_products": [{"name": name, "quantity": _money(quantity), "revenue": _money(value)}
                         for name, quantity, value in top_products],
    }
