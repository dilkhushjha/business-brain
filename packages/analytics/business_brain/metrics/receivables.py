from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import CustomerModel, SaleModel

def receivables_summary(db: Session, business_id: UUID) -> dict[str, Any]:
    today=date.today()
    rows=db.execute(select(SaleModel.total_amount,SaleModel.paid_amount,SaleModel.due_date).where(SaleModel.business_id==business_id)).all()
    outstanding=Decimal("0"); overdue=Decimal("0"); buckets={"0_30":Decimal("0"),"31_60":Decimal("0"),"61_90":Decimal("0"),"90_plus":Decimal("0")}
    for total,paid,due in rows:
        amount=max(Decimal(total or 0)-Decimal(paid or 0),Decimal("0")); outstanding+=amount
        if due and amount>0 and due<today:
            days=(today-due).days; overdue+=amount
            key="0_30" if days<=30 else "31_60" if days<=60 else "61_90" if days<=90 else "90_plus"; buckets[key]+=amount
    return {"outstanding":float(outstanding),"overdue":float(overdue),"overdue_pct":round(float(overdue/outstanding*100),2) if outstanding else 0,"buckets":{k:float(v) for k,v in buckets.items()}}

def overdue_customers(db: Session,business_id: UUID,limit:int=10)->list[dict[str,Any]]:
    today=date.today(); rows=db.execute(select(CustomerModel.name,SaleModel.total_amount,SaleModel.paid_amount,SaleModel.due_date).join(SaleModel,SaleModel.customer_id==CustomerModel.id).where(SaleModel.business_id==business_id,SaleModel.due_date<today)).all(); agg={}
    for name,total,paid,due in rows:
        outstanding=max(Decimal(total or 0)-Decimal(paid or 0),Decimal("0"));
        if outstanding: x=agg.setdefault(name,[Decimal("0"),0]);x[0]+=outstanding;x[1]=max(x[1],(today-due).days)
    return [{"name":n,"overdue_amount":float(v[0]),"days_overdue":v[1]} for n,v in sorted(agg.items(),key=lambda x:x[1][0],reverse=True)[:limit]]
