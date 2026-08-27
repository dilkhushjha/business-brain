from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.metrics.kpis import KPI, average_invoice_value, growth
from packages.analytics.business_brain.metrics.time_windows import current_month, previous_month
from packages.analytics.business_brain.query.sales import sales_summary


def monthly_sales_kpis(db: Session, business_id: UUID, as_of: date) -> list[KPI]:
    current = current_month(as_of)
    previous = previous_month(as_of)
    now = sales_summary(db, business_id, current.start, current.end)
    prior = sales_summary(db, business_id, previous.start, previous.end)

    revenue_change = growth(now.revenue, prior.revenue)
    aiv = average_invoice_value(now.revenue, now.invoice_count)
    prior_aiv = average_invoice_value(prior.revenue, prior.invoice_count)
    aiv_change = None if aiv is None or prior_aiv is None else growth(aiv, prior_aiv)

    return [
        KPI("revenue", now.revenue, "INR", "current_month", prior.revenue, revenue_change),
        KPI("invoice_count", Decimal(now.invoice_count), "count", "current_month", Decimal(prior.invoice_count), growth(Decimal(now.invoice_count), Decimal(prior.invoice_count))),
        KPI("units_sold", now.units, "units", "current_month", prior.units, growth(now.units, prior.units)),
        KPI("average_invoice_value", aiv, "INR", "current_month", prior_aiv, aiv_change),
    ]
