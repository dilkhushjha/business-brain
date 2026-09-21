from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.api.connector_auth import require_business_access
from packages.analytics.business_brain.financial_integrity import audit_financial_linkage
from packages.shared.database.session import get_db

router = APIRouter(prefix="/financial-integrity", tags=["analytics"])


@router.get("/{business_id}")
def financial_integrity(
    business_id: UUID,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    return audit_financial_linkage(db, business_id)
