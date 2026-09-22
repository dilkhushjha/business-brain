from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.api.connector_auth import require_business_access
from packages.analytics.business_brain.context.builder import build_business_context
from packages.shared.database.session import get_db

router = APIRouter(prefix="/risks", tags=["risks"])


@router.get("/{business_id}")
def get_business_risks(
    business_id: UUID,
    as_of: date | None = None,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    context = build_business_context(db, business_id, as_of or date.today())
    return {
        "business_id": business_id.hex,
        "risks": [
            {
                "code": risk.code,
                "title": risk.title,
                "level": risk.level,
                "score": str(risk.score),
                "confidence": str(risk.confidence),
                "signal_codes": risk.signal_codes,
                "evidence": risk.evidence,
                "explanation": risk.explanation,
                "recommended_next_step": risk.recommended_next_step,
            }
            for risk in context.risks
        ],
    }
