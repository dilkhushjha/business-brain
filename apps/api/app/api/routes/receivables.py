from uuid import UUID
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.receivables import receivables_summary,overdue_customers
from packages.shared.database.session import get_db
router=APIRouter(prefix="/receivables",tags=["analytics"])
@router.get("/{business_id}/summary")
def summary(business_id:UUID,db:Session=Depends(get_db)): return receivables_summary(db,business_id)
@router.get("/{business_id}/overdue")
def overdue(business_id:UUID,limit:int=10,db:Session=Depends(get_db)): return overdue_customers(db,business_id,limit)
