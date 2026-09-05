from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.customer_concentration import customer_concentration
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.session import get_db

router = APIRouter(prefix="/customer-risk", tags=["analytics"])

@router.get("/{business_id}/concentration")
def concentration(business_id: UUID, days: int = 90, limit: int = 5, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return customer_concentration(db, business_id, days=days, limit=limit)
