from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from packages.analytics.business_brain.service import monthly_sales_kpis
from packages.analytics.business_brain.query.sales import sales_summary
from packages.shared.database.session import get_db

router = APIRouter(prefix="/kpis", tags=["analytics"])


@router.get("/sales/{business_id}")
def sales_kpis(business_id: UUID, as_of: date | None = None, db: Session = Depends(get_db)):
    effective_date = as_of or date.today()
    monthly = monthly_sales_kpis(db, business_id, effective_date)
    historical = sales_summary(db, business_id, date(2000, 1, 1), effective_date)

    response = [
        {
            "name": kpi.name,
            "value": str(kpi.value) if kpi.value is not None else None,
            "unit": kpi.unit,
            "period": kpi.period,
            "comparison_value": str(kpi.comparison_value) if kpi.comparison_value is not None else None,
            "change": str(kpi.change) if kpi.change is not None else None,
        }
        for kpi in monthly
    ]
    response.insert(0, {
        "name": "total_revenue",
        "value": str(historical.revenue),
        "unit": "INR",
        "period": "all_time",
        "comparison_value": None,
        "change": None,
    })
    response.insert(1, {
        "name": "total_invoice_count",
        "value": str(historical.invoice_count),
        "unit": "count",
        "period": "all_time",
        "comparison_value": None,
        "change": None,
    })
    return response
