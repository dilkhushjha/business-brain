from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import CustomerModel, ProductModel, SaleLineModel, SaleModel


def _daily_product_revenue(db: Session, business_id: UUID, product_id: UUID, start: date, end: date):
    rows = db.execute(select(SaleModel.transaction_date, func.sum(SaleLineModel.quantity * SaleLineModel.unit_price))
        .join(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
        .where(SaleModel.business_id == business_id, SaleLineModel.product_id == product_id,
               SaleModel.transaction_date.between(start, end))
        .group_by(SaleModel.transaction_date).order_by(SaleModel.transaction_date)).all()
    return [(d, float(v or 0)) for d, v in rows]


def performance_anomalies(db: Session, business_id: UUID, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    end = date.today(); current_start = end - timedelta(days=max(1, days) - 1)
    baseline_end = current_start - timedelta(days=1); baseline_start = baseline_end - timedelta(days=days - 1)
    products = db.execute(select(ProductModel.id, ProductModel.name).join(SaleLineModel, SaleLineModel.product_id == ProductModel.id)
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id).where(SaleModel.business_id == business_id)
        .group_by(ProductModel.id, ProductModel.name)).all()
    anomalies = []
    for pid, name in products:
        cur = db.scalar(select(func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price), 0)).join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
            .where(SaleModel.business_id == business_id, SaleLineModel.product_id == pid, SaleModel.transaction_date.between(current_start, end))) or 0
        base = db.scalar(select(func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price), 0)).join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
            .where(SaleModel.business_id == business_id, SaleLineModel.product_id == pid, SaleModel.transaction_date.between(baseline_start, baseline_end))) or 0
        if base:
            change = (float(cur) - float(base)) / float(base) * 100
            if abs(change) >= 25:
                anomalies.append({"type": "product", "name": name, "current_revenue": float(cur), "baseline_revenue": float(base), "change_pct": round(change, 2), "severity": "high" if abs(change) >= 50 else "medium"})
    return sorted(anomalies, key=lambda x: abs(x["change_pct"]), reverse=True)[:limit]
