from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from packages.analytics.business_brain.service import monthly_sales_kpis
from packages.shared.database.session import get_db

router = APIRouter(prefix="/kpis", tags=["analytics"])


@router.get("/sales/{business_id}")
def sales_kpis(business_id: UUID, as_of: date | None = None, db: Session = Depends(get_db)):
    effective_date = as_of or date.today()
    return [
        {
            "name": kpi.name,
            "value": str(kpi.value) if kpi.value is not None else None,
            "unit": kpi.unit,
            "period": kpi.period,
            "comparison_value": str(kpi.comparison_value) if kpi.comparison_value is not None else None,
            "change": str(kpi.change) if kpi.change is not None else None,
        }
        for kpi in monthly_sales_kpis(db, business_id, effective_date)
    ]
