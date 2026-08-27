from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.context.builder import build_business_context
from packages.analytics.business_brain.context.serializer import serialize_context


def retrieve_context(db: Session, business_id: UUID, as_of: date) -> dict:
    return serialize_context(build_business_context(db, business_id, as_of))
