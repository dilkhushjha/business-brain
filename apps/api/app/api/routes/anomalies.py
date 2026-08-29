from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.anomalies import performance_anomalies
from packages.shared.database.session import get_db

router = APIRouter(prefix="/anomalies", tags=["analytics"])

@router.get("/{business_id}")
def anomalies(business_id: UUID, days: int = 30, limit: int = 10, db: Session = Depends(get_db)):
    return performance_anomalies(db, business_id, days=days, limit=limit)
