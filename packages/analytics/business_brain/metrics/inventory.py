from __future__ import annotations
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import select
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
