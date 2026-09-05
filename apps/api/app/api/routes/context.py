from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from packages.analytics.business_brain.context.builder import build_business_context
from packages.analytics.business_brain.context.serializer import serialize_context
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.session import get_db

router = APIRouter(prefix="/context", tags=["intelligence"])


@router.get("/{business_id}")
def business_context(business_id: UUID, as_of: date | None = None, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    context = build_business_context(db, business_id, as_of or date.today())
    return serialize_context(context)
