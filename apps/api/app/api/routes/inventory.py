from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.inventory import inventory_signals, slow_moving_products
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.session import get_db
router=APIRouter(prefix="/inventory",tags=["analytics"])
@router.get("/{business_id}/signals")
def signals(business_id:UUID,days:int=30,limit:int=10,db:Session=Depends(get_db),_auth:dict=Depends(require_business_access)): return inventory_signals(db,business_id,days,limit)
@router.get("/{business_id}/slow-moving")
def slow_moving(business_id:UUID,days:int=30,threshold:float=40,limit:int=10,db:Session=Depends(get_db),_auth:dict=Depends(require_business_access)): return slow_moving_products(db,business_id,days,threshold,limit)
