from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.product_risk import product_concentration, product_momentum
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.session import get_db

router = APIRouter(prefix="/product-risk", tags=["analytics"])

@router.get("/{business_id}/concentration")
def concentration(business_id: UUID, top_n: int = 5, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return product_concentration(db, business_id, top_n=top_n)

@router.get("/{business_id}/momentum")
def momentum(business_id: UUID, days: int = 30, threshold: float = 30, limit: int = 5, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return product_momentum(db, business_id, days=days, threshold=threshold, limit=limit)
