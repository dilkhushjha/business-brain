from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.api.connector_auth import require_business_access
from packages.analytics.business_brain.readiness import build_business_readiness
from packages.shared.database.session import get_db

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.get("/{business_id}")
def readiness(
    business_id: UUID,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Return a read-only assessment of whether current business data is ready for insights."""
    return build_business_readiness(db, business_id, as_of=date.today())
