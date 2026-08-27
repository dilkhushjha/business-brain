from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from packages.analytics.business_brain.recommendations.engine import recommend
from packages.shared.database.session import get_db

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{business_id}")
def recommendations(business_id: UUID, as_of: date | None = None, db: Session = Depends(get_db)):
    results = recommend(db, business_id, as_of or date.today())
    return [
        {
            "code": item.code,
            "title": item.title,
            "priority": item.priority,
            "confidence": str(item.confidence),
            "rationale": item.rationale,
            "evidence": item.evidence,
            "actions": item.actions,
        }
        for item in results
    ]
