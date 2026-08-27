from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from packages.analytics.business_brain.metrics.time_windows import current_month
from packages.analytics.business_brain.query.dimensions import sales_by_customer, sales_by_product
from packages.shared.database.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _window(as_of: date | None):
    return current_month(as_of or date.today())


def _serialize(items):
    return [
        {
            "id": str(item.key),
            "label": item.label,
            "revenue": str(item.revenue),
            "units": str(item.units),
            "invoice_count": item.invoice_count,
        }
        for item in items
    ]


@router.get("/sales/{business_id}/products")
def products(business_id: UUID, as_of: date | None = None, limit: int = 20, db: Session = Depends(get_db)):
    window = _window(as_of)
    return _serialize(sales_by_product(db, business_id, window.start, window.end, limit))


@router.get("/sales/{business_id}/customers")
def customers(business_id: UUID, as_of: date | None = None, limit: int = 20, db: Session = Depends(get_db)):
    window = _window(as_of)
    return _serialize(sales_by_customer(db, business_id, window.start, window.end, limit))
