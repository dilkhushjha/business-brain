from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.metrics.customer_risk import declining_customers
from packages.analytics.business_brain.service import monthly_sales_kpis
from packages.analytics.business_brain.signals.models import Signal
from packages.analytics.business_brain.signals.rules import (
    detect_customer_decline_signals,
    detect_kpi_signals,
)


def detect_signals(db: Session, business_id: UUID, as_of: date) -> list[Signal]:
    kpis = monthly_sales_kpis(db, business_id, as_of)
    signals = detect_kpi_signals(kpis)
    signals.extend(detect_customer_decline_signals(declining_customers(db, business_id)))
    return signals
