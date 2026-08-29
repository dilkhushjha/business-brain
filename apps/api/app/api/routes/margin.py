from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.margin import margin_summary, low_margin_products
from packages.shared.database.session import get_db

router=APIRouter(prefix="/margin",tags=["analytics"])

@router.get("/{business_id}/summary")
def summary(business_id:UUID,days:int=30,db:Session=Depends(get_db)): return margin_summary(db,business_id,days)

@router.get("/{business_id}/low-margin")
def low_margin(business_id:UUID,days:int=30,threshold:float=10,limit:int=10,db:Session=Depends(get_db)): return low_margin_products(db,business_id,days,threshold,limit)
