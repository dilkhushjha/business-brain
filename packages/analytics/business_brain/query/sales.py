from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import SaleLineModel, SaleModel


@dataclass(frozen=True)
class SalesSummary:
    revenue: Decimal
    invoice_count: int
    units: Decimal


def sales_summary(db: Session, business_id: UUID, start: date, end: date) -> SalesSummary:
    """Revenue and invoice_count are computed directly from SaleModel, not
    through the sale_lines join -- joining sale_lines duplicates each sale
    row once per line, which silently doubled (or worse) both total_amount
    and invoice_count for any multi-line invoice. units_sold genuinely needs
    the join (we want the total quantity across all lines), so it's kept as
    a separate query rather than trying to force everything into one
    statement."""
    sale_filter = (
        SaleModel.business_id == business_id,
        SaleModel.transaction_date >= start,
        SaleModel.transaction_date <= end,
    )
    revenue, invoices = db.execute(
        select(
            func.coalesce(func.sum(SaleModel.total_amount), 0),
            func.count(SaleModel.id),
        ).where(*sale_filter)
    ).one()
    units = db.execute(
        select(func.coalesce(func.sum(SaleLineModel.quantity), 0))
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
        .where(*sale_filter)
    ).scalar()
    return SalesSummary(Decimal(revenue), int(invoices), Decimal(units))
