from __future__ import annotations
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import ProductModel, SaleLineModel, SaleModel


def margin_summary(db: Session, business_id: UUID, days: int = 30) -> dict[str, Any]:
    end = date.today(); start = end - timedelta(days=days - 1)
    rows = db.execute(select(SaleLineModel.quantity, SaleLineModel.unit_price, SaleLineModel.cost_price).join(SaleModel, SaleModel.id == SaleLineModel.sale_id).where(SaleModel.business_id == business_id, SaleModel.transaction_date.between(start, end))).all()
    revenue = sum(Decimal(q or 0) * Decimal(p or 0) for q,p,c in rows)
    cost = sum(Decimal(q or 0) * Decimal(c or 0) for q,p,c in rows if c is not None)
    covered = sum(Decimal(q or 0) * Decimal(p or 0) for q,p,c in rows if c is not None)
    profit = covered - cost
    margin = (profit / covered * 100) if covered else None
    return {"days": days, "revenue": float(revenue), "cost": float(cost), "gross_profit": float(profit), "gross_margin_pct": round(float(margin),2) if margin is not None else None, "cost_coverage_pct": round(float(covered/revenue*100),2) if revenue else 0}


def low_margin_products(db: Session, business_id: UUID, days: int = 30, threshold: float = 10, limit: int = 10) -> list[dict[str, Any]]:
    end=date.today(); start=end-timedelta(days=days-1)
    rows=db.execute(select(ProductModel.name, SaleLineModel.quantity, SaleLineModel.unit_price, SaleLineModel.cost_price).join(SaleLineModel, SaleLineModel.product_id==ProductModel.id).join(SaleModel, SaleModel.id==SaleLineModel.sale_id).where(ProductModel.business_id==business_id,SaleModel.business_id==business_id,SaleModel.transaction_date.between(start,end),SaleLineModel.cost_price.is_not(None))).all()
    agg={}
    for name,q,p,c in rows:
        rev=float(Decimal(q)*Decimal(p)); cost=float(Decimal(q)*Decimal(c)); x=agg.setdefault(name,[0.0,0.0]); x[0]+=rev; x[1]+=cost
    out=[]
    for name,(rev,cost) in agg.items():
        margin=(rev-cost)/rev*100 if rev else 0
        if margin <= threshold: out.append({"name":name,"revenue":round(rev,2),"gross_profit":round(rev-cost,2),"margin_pct":round(margin,2),"severity":"high" if margin<0 else "medium"})
    return sorted(out,key=lambda x:x["margin_pct"])[:limit]
