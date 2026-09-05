from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import SaleModel
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.session import get_db

router = APIRouter(prefix="/trends", tags=["analytics"])


@router.get("/revenue/{business_id}")
def revenue_trend(
    business_id: UUID,
    days: int = 30,
    as_of: date | None = None,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    days = max(7, min(days, 365))
    end = as_of or date.today()
    start = end - timedelta(days=days - 1)
    rows = db.execute(
        select(
            SaleModel.transaction_date,
            func.coalesce(func.sum(SaleModel.total_amount), 0).label("revenue"),
        )
        .where(
            SaleModel.business_id == business_id,
            SaleModel.transaction_date.between(start, end),
        )
        .group_by(SaleModel.transaction_date)
        .order_by(SaleModel.transaction_date)
    ).all()
    values = {day: float(revenue or 0) for day, revenue in rows}
    return [
        {"date": (start + timedelta(days=i)).isoformat(), "revenue": values.get(start + timedelta(days=i), 0.0)}
        for i in range(days)
    ]
