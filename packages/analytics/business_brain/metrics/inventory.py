from __future__ import annotations
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import ProductModel, SaleLineModel, SaleModel

def inventory_signals(db: Session, business_id: UUID, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    end=date.today(); start=end-timedelta(days=days-1)
    rows=db.execute(select(ProductModel.name,SaleLineModel.quantity,SaleLineModel.unit_price).join(SaleLineModel,SaleLineModel.product_id==ProductModel.id).join(SaleModel,SaleModel.id==SaleLineModel.sale_id).where(ProductModel.business_id==business_id,SaleModel.business_id==business_id,SaleModel.transaction_date.between(start,end))).all()
    agg={}
    for name,q,p in rows:
        x=agg.setdefault(name,[Decimal("0"),Decimal("0")]);x[0]+=Decimal(q or 0);x[1]+=Decimal(q or 0)*Decimal(p or 0)
    out=[]
    for name,(qty,revenue) in agg.items():
        daily=qty/Decimal(days) if days else Decimal("0"); days_of_demand=Decimal("0") if daily==0 else Decimal("30")
        out.append({"name":name,"units_sold":float(qty),"revenue":float(revenue),"avg_daily_units":round(float(daily),2),"signal":"fast_mover" if daily>=2 else "normal","recommended_review":"Prioritize replenishment" if daily>=2 else None})
    return sorted(out,key=lambda x:x["units_sold"],reverse=True)[:limit]


def slow_moving_products(db: Session, business_id: UUID, days: int = 30, threshold: float = 40, limit: int = 10) -> list[dict[str, Any]]:
    """Products whose sales velocity has dropped materially vs. the prior
    period of the same length. Approximates 'slow-moving inventory' from
    sales velocity alone, since this schema has no stock-on-hand tracking
    to compute true days-of-inventory-remaining."""
    end = date.today(); cur_start = end - timedelta(days=days - 1)
    prev_end = cur_start - timedelta(days=1); prev_start = prev_end - timedelta(days=days - 1)
    products = db.execute(select(ProductModel.id, ProductModel.name).where(ProductModel.business_id == business_id)).all()
    result = []
    for pid, name in products:
        def units_in(lo, hi):
            return float(db.scalar(
                select(func.coalesce(func.sum(SaleLineModel.quantity), 0))
                .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
                .where(SaleLineModel.product_id == pid, SaleModel.business_id == business_id,
                       SaleModel.transaction_date.between(lo, hi))
            ) or 0)
        cur = units_in(cur_start, end)
        prev = units_in(prev_start, prev_end)
        if prev and (prev - cur) / prev * 100 >= threshold:
            change_pct = round((cur - prev) / prev * 100, 2)
            result.append({
                "name": name, "current_units": cur, "previous_units": prev,
                "change_pct": change_pct,
                "severity": "high" if change_pct <= -70 else "medium",
            })
    return sorted(result, key=lambda x: x["change_pct"])[:limit]
