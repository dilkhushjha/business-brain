from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.api.connector_auth import require_business_access
from packages.analytics.business_brain.data_quality import audit_data_quality
from packages.shared.database.session import get_db

router = APIRouter(prefix="/data-integrity", tags=["data-integrity"])


@router.get("/{business_id}")
def data_integrity(
    business_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Return a read-only audit of import/canonical data quality."""
    return audit_data_quality(db, business_id, limit=limit)
