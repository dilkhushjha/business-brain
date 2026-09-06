from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.supplier_risk import supplier_concentration, supplier_price_increases
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.session import get_db

router = APIRouter(prefix="/supplier-risk", tags=["analytics"])

@router.get("/{business_id}/concentration")
def concentration(business_id: UUID, top_n: int = 5, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return supplier_concentration(db, business_id, top_n=top_n)

@router.get("/{business_id}/price-increases")
def price_increases(business_id: UUID, days: int = 30, threshold: float = 15, limit: int = 10, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return supplier_price_increases(db, business_id, days=days, threshold=threshold, limit=limit)
