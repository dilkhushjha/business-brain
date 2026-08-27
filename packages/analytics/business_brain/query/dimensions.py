from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import CustomerModel, ProductModel, SaleLineModel, SaleModel


@dataclass(frozen=True)
class DimensionResult:
    key: UUID
    label: str
    revenue: Decimal
    units: Decimal
    invoice_count: int


def sales_by_product(db: Session, business_id: UUID, start: date, end: date, limit: int = 20) -> list[DimensionResult]:
    stmt = (
        select(
            ProductModel.id,
            ProductModel.name,
            func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price), 0),
            func.coalesce(func.sum(SaleLineModel.quantity), 0),
            func.count(func.distinct(SaleModel.id)),
        )
        .join(SaleLineModel, SaleLineModel.product_id == ProductModel.id)
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
        .where(
            ProductModel.business_id == business_id,
            SaleModel.transaction_date >= start,
            SaleModel.transaction_date <= end,
        )
        .group_by(ProductModel.id, ProductModel.name)
        .order_by(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price).desc())
        .limit(limit)
    )
    return [DimensionResult(row[0], row[1], Decimal(row[2]), Decimal(row[3]), int(row[4])) for row in db.execute(stmt)]


def sales_by_customer(db: Session, business_id: UUID, start: date, end: date, limit: int = 20) -> list[DimensionResult]:
    stmt = (
        select(
            CustomerModel.id,
            CustomerModel.name,
            func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price), 0),
            func.coalesce(func.sum(SaleLineModel.quantity), 0),
            func.count(func.distinct(SaleModel.id)),
        )
        .join(SaleModel, SaleModel.customer_id == CustomerModel.id)
        .join(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
        .where(
            CustomerModel.business_id == business_id,
            SaleModel.transaction_date >= start,
            SaleModel.transaction_date <= end,
        )
        .group_by(CustomerModel.id, CustomerModel.name)
        .order_by(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price).desc())
        .limit(limit)
    )
    return [DimensionResult(row[0], row[1], Decimal(row[2]), Decimal(row[3]), int(row[4])) for row in db.execute(stmt)]
