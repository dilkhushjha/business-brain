from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.expenses import expense_summary, expense_spikes
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.session import get_db

router = APIRouter(prefix="/expenses", tags=["analytics"])

@router.get("/{business_id}/summary")
def summary(business_id: UUID, days: int = 30, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return expense_summary(db, business_id, days=days)

@router.get("/{business_id}/spikes")
def spikes(business_id: UUID, days: int = 30, threshold: float = 30, limit: int = 10, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return expense_spikes(db, business_id, days=days, threshold=threshold, limit=limit)
