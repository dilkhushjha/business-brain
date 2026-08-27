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
    stmt = select(
        func.coalesce(func.sum(SaleModel.total_amount), 0),
        func.count(SaleModel.id),
        func.coalesce(func.sum(SaleLineModel.quantity), 0),
    ).join(SaleLineModel, SaleLineModel.sale_id == SaleModel.id).where(
        SaleModel.business_id == business_id,
        SaleModel.transaction_date >= start,
        SaleModel.transaction_date <= end,
    )
    revenue, invoices, units = db.execute(stmt).one()
    return SalesSummary(Decimal(revenue), int(invoices), Decimal(units))
