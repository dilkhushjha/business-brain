from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.inventory import inventory_signals
from packages.shared.database.session import get_db
router=APIRouter(prefix="/inventory",tags=["analytics"])
@router.get("/{business_id}/signals")
def signals(business_id:UUID,days:int=30,limit:int=10,db:Session=Depends(get_db)): return inventory_signals(db,business_id,days,limit)
