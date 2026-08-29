from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.customer_risk import inactive_customers, declining_customers, customer_concentration
from packages.shared.database.session import get_db

router = APIRouter(prefix="/customer-risk", tags=["analytics"])

@router.get("/{business_id}/inactive")
def inactive(business_id: UUID, inactive_days: int = 45, limit: int = 10, db: Session = Depends(get_db)):
    return inactive_customers(db, business_id, inactive_days=inactive_days, limit=limit)

@router.get("/{business_id}/declining")
def declining(business_id: UUID, days: int = 30, threshold: float = 25, limit: int = 10, db: Session = Depends(get_db)):
    return declining_customers(db, business_id, days=days, threshold=threshold, limit=limit)

@router.get("/{business_id}/concentration")
def concentration(business_id: UUID, top_n: int = 5, db: Session = Depends(get_db)):
    return customer_concentration(db, business_id, top_n=top_n)
