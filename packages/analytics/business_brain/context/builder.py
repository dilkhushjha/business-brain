from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.context.models import BusinessContext, Evidence
from packages.analytics.business_brain.recommendations.engine import recommend
from packages.analytics.business_brain.service import monthly_sales_kpis
from packages.analytics.business_brain.signals.engine import detect_signals


def build_business_context(db: Session, business_id: UUID, as_of: date) -> BusinessContext:
    kpis = monthly_sales_kpis(db, business_id, as_of)
    signals = detect_signals(db, business_id, as_of)
    recommendations = recommend(db, business_id, as_of)
    evidence = [
        Evidence(
            source="kpi_engine",
            metric=kpi.name,
            value=kpi.value,
            period=kpi.period,
            metadata={
                "comparison_value": str(kpi.comparison_value) if kpi.comparison_value is not None else None,
                "change": str(kpi.change) if kpi.change is not None else None,
            },
        )
        for kpi in kpis
    ]
    return BusinessContext(
        business_id=business_id,
        entities=[],
        evidence=evidence,
        signals=signals,
        recommendations=recommendations,
    )
