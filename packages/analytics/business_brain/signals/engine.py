from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.metrics.customer_risk import declining_customers, inactive_customers
from packages.analytics.business_brain.metrics.inventory import slow_moving_products
from packages.analytics.business_brain.metrics.margin import low_margin_products
from packages.analytics.business_brain.metrics.receivables import overdue_customers
from packages.analytics.business_brain.service import monthly_sales_kpis
from packages.analytics.business_brain.signals.models import Signal
from packages.analytics.business_brain.signals.rules import (
    detect_customer_decline_signals,
    detect_customer_inactivity_signals,
    detect_kpi_signals,
    detect_margin_signals,
    detect_receivables_signals,
    detect_slow_moving_product_signals,
)


def detect_signals(db: Session, business_id: UUID, as_of: date) -> list[Signal]:
    kpis = monthly_sales_kpis(db, business_id, as_of)
    signals = detect_kpi_signals(kpis)
    signals.extend(detect_customer_decline_signals(declining_customers(db, business_id)))
    signals.extend(detect_customer_inactivity_signals(inactive_customers(db, business_id)))
    signals.extend(detect_margin_signals(low_margin_products(db, business_id)))
    signals.extend(detect_receivables_signals(overdue_customers(db, business_id)))
    signals.extend(detect_slow_moving_product_signals(slow_moving_products(db, business_id)))
    return signals
