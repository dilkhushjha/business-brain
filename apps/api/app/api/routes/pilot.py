from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.api.connector_auth import require_business_access
from packages.analytics.business_brain.pilot_readiness import audit_pilot_readiness
from packages.shared.database.session import get_db

router = APIRouter(prefix="/pilot", tags=["pilot"])


@router.get("/{business_id}/readiness")
def pilot_readiness(
    business_id: UUID,
    as_of: date | None = None,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Return a read-only readiness gate before onboarding a real business."""
    return audit_pilot_readiness(db, business_id, as_of or date.today())
