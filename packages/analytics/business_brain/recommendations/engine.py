from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.recommendations.models import RecommendationContext
from packages.analytics.business_brain.recommendations.rules import generate_recommendations
from packages.analytics.business_brain.signals.engine import detect_signals


def recommend(db: Session, business_id: UUID, as_of: date):
    signals = detect_signals(db, business_id, as_of)
    return generate_recommendations(RecommendationContext(signals=signals, drivers=[]))
