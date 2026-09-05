from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from packages.analytics.business_brain.metrics.business_performance import top_customers, top_products
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.session import get_db

router = APIRouter(prefix="/performance", tags=["analytics"])


@router.get("/{business_id}/products")
def products(business_id: UUID, days: int = 30, limit: int = 10, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return top_products(db, business_id, days=days, limit=limit)


@router.get("/{business_id}/customers")
def customers(business_id: UUID, days: int = 30, limit: int = 10, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    return top_customers(db, business_id, days=days, limit=limit)
