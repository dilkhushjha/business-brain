from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from packages.analytics.business_brain.signals.engine import detect_signals
from packages.shared.database.session import get_db

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/{business_id}")
def signals(business_id: UUID, as_of: date | None = None, db: Session = Depends(get_db)):
    results = detect_signals(db, business_id, as_of or date.today())
    return [
        {
            "code": signal.code,
            "title": signal.title,
            "severity": signal.severity,
            "confidence": str(signal.confidence),
            "metric": signal.metric,
            "current_value": str(signal.current_value) if signal.current_value is not None else None,
            "baseline_value": str(signal.baseline_value) if signal.baseline_value is not None else None,
            "change": str(signal.change) if signal.change is not None else None,
            "evidence": signal.evidence,
            "recommended_next_step": signal.recommended_next_step,
        }
        for signal in results
    ]
