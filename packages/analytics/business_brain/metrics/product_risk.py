from __future__ import annotations
from datetime import date, timedelta
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import ProductModel, SaleLineModel, SaleModel


def product_concentration(db: Session, business_id: UUID, top_n: int = 5) -> dict[str, Any]:
    rows = db.execute(select(ProductModel.name, func.sum(SaleLineModel.quantity * SaleLineModel.unit_price).label("revenue")).join(SaleLineModel, SaleLineModel.product_id == ProductModel.id).join(SaleModel, SaleModel.id == SaleLineModel.sale_id).where(ProductModel.business_id == business_id, SaleModel.business_id == business_id).group_by(ProductModel.id, ProductModel.name).order_by(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price).desc())).all()
    total = sum(float(r.revenue or 0) for r in rows)
    top = [{"name": r.name, "revenue": float(r.revenue or 0), "share_pct": round(float(r.revenue or 0) / total * 100, 2) if total else 0} for r in rows[:top_n]]
    share = round(sum(x["share_pct"] for x in top), 2)
    risk = "high" if share >= 60 or (top and top[0]["share_pct"] >= 35) else "medium" if share >= 40 or (top and top[0]["share_pct"] >= 20) else "low"
    return {"total_revenue": total, "top_products": top, "top_n": top_n, "top_share_pct": share, "risk": risk}


def product_momentum(db: Session, business_id: UUID, days: int = 30, threshold: float = 30, limit: int = 5) -> list[dict[str, Any]]:
    end = date.today(); cur_start = end - timedelta(days=days - 1); prev_end = cur_start - timedelta(days=1); prev_start = prev_end - timedelta(days=days - 1)
    rows = db.execute(select(ProductModel.id, ProductModel.name).where(ProductModel.business_id == business_id)).all()
    result=[]
    for pid, name in rows:
        def revenue(a,b):
            return float(db.scalar(select(func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price),0)).join(SaleModel, SaleModel.id == SaleLineModel.sale_id).where(SaleModel.business_id==business_id, SaleModel.transaction_date.between(a,b), SaleLineModel.product_id==pid)) or 0)
        cur=revenue(cur_start,end); prev=revenue(prev_start,prev_end)
        if prev and abs((cur-prev)/prev*100) >= threshold:
            change=(cur-prev)/prev*100
            result.append({"name":name,"current_revenue":cur,"previous_revenue":prev,"change_pct":round(change,2),"direction":"up" if change>0 else "down","severity":"high" if abs(change)>=50 else "medium"})
    return sorted(result,key=lambda x:abs(x["change_pct"]),reverse=True)[:limit]
