from datetime import date
from uuid import UUID
from sqlalchemy.orm import Session
from packages.analytics.business_brain.query.sales import sales_summary

def historical_revenue(db: Session, business_id: UUID, as_of: date):
    return sales_summary(db, business_id, date(2000, 1, 1), as_of).revenue
