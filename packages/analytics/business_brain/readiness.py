from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.analytics.business_brain.business_integrity import audit_business_integrity
from packages.shared.database.models import (
    CustomerModel,
    ExpenseModel,
    ProductModel,
    PurchaseModel,
    SaleModel,
    SupplierModel,
)


def _count(db: Session, model, business_id: UUID) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(model).where(model.business_id == business_id)
        )
        or 0
    )


def _date_range(db: Session, model, business_id: UUID) -> tuple[date | None, date | None]:
    return db.execute(
        select(func.min(model.transaction_date), func.max(model.transaction_date))
        .where(model.business_id == business_id)
    ).one()


def build_business_readiness(db: Session, business_id: UUID, as_of: date | None = None) -> dict[str, Any]:
    sales_count = _count(db, SaleModel, business_id)
    purchase_count = _count(db, PurchaseModel, business_id)
    expense_count = _count(db, ExpenseModel, business_id)
    customer_count = _count(db, CustomerModel, business_id)
    supplier_count = _count(db, SupplierModel, business_id)
    product_count = _count(db, ProductModel, business_id)

    sale_start, sale_end = _date_range(db, SaleModel, business_id)
    purchase_start, purchase_end = _date_range(db, PurchaseModel, business_id)

    integrity = audit_business_integrity(db, business_id, as_of=as_of)
    has_transaction_data = sales_count > 0 or purchase_count > 0

    if not has_transaction_data:
        status = "insufficient_data"
        headline = "Import business transactions before relying on Business Brain."
    elif integrity["status"] == "attention_required":
        status = "review_required"
        headline = "Business data is available, but source exceptions should be reviewed."
    elif sales_count == 0:
        status = "partial"
        headline = "Purchase data is available; sales data is still missing."
    else:
        status = "ready"
        headline = "Business Brain has a usable transaction base and no current integrity exceptions."

    domains = []
    if sales_count:
        domains.append("sales")
    if purchase_count:
        domains.append("purchases")
    if expense_count:
        domains.append("expenses")
    if customer_count:
        domains.append("customers")
    if supplier_count:
        domains.append("suppliers")
    if product_count:
        domains.append("products")

    return {
        "status": status,
        "headline": headline,
        "as_of": (as_of or date.today()).isoformat(),
        "transaction_coverage": {
            "sales_count": sales_count,
            "purchase_count": purchase_count,
            "expense_count": expense_count,
            "sales_period": {"from": sale_start, "to": sale_end},
            "purchase_period": {"from": purchase_start, "to": purchase_end},
        },
        "entity_coverage": {
            "customers": customer_count,
            "suppliers": supplier_count,
            "products": product_count,
        },
        "domains_present": domains,
        "integrity": {
            "status": integrity["status"],
            "issue_count": integrity["issue_count"],
            "affected_domains": integrity["affected_domains"],
        },
        "limitations": (
            ["No sales or purchase transactions are currently available."]
            if not has_transaction_data
            else (
                ["Sales data is missing, so revenue and sales-performance conclusions will be limited."]
                if sales_count == 0
                else []
            )
        ),
    }
