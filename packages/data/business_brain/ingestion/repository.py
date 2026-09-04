from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.canonicalize import canonicalize_sale_row
from packages.shared.database.models import CustomerModel, ProductModel, SaleLineModel, SaleModel


def _find_customer(db: Session, business_id: UUID, name: str | None) -> CustomerModel | None:
    if not name:
        return None
    stmt = select(CustomerModel).where(CustomerModel.business_id == business_id, CustomerModel.name == name)
    return db.execute(stmt).scalar_one_or_none()


def _get_or_create_product(db: Session, business_id: UUID, name: str) -> ProductModel:
    stmt = select(ProductModel).where(ProductModel.business_id == business_id, ProductModel.name == name)
    product = db.execute(stmt).scalar_one_or_none()
    if product:
        return product
    product = ProductModel(business_id=business_id, name=name)
    db.add(product)
    db.flush()
    return product


def persist_sales(db: Session, business_id: UUID, rows: list[dict]) -> int:
    """Persist canonical sales without committing; caller owns the transaction.

    Known boundary: an invoice that already exists (matched by
    business_id + invoice_number) is skipped entirely, including its
    due_date/paid_amount. If a business re-exports their sales register
    later with an invoice now marked paid, that update will NOT be applied
    here -- this only ingests new invoices, it doesn't reconcile changes to
    ones already stored. Fixing that is a deliberate follow-up (needs a
    real decision on what's safe to overwrite vs. what a human entered
    directly), not a silent gap in this pass.
    """
    created = 0
    for raw in rows:
        row = canonicalize_sale_row(raw)
        invoice = row["invoice_number"]
        if not invoice:
            continue
        existing = db.execute(select(SaleModel).where(SaleModel.business_id == business_id, SaleModel.invoice_number == invoice)).scalar_one_or_none()
        if existing:
            continue
        customer = _find_customer(db, business_id, row["customer_name"])
        if row["customer_name"] and customer is None:
            customer = CustomerModel(business_id=business_id, name=row["customer_name"])
            db.add(customer)
            db.flush()
        product = _get_or_create_product(db, business_id, row["product_name"])
        sale = SaleModel(business_id=business_id, customer_id=customer.id if customer else None, transaction_date=row["transaction_date"], invoice_number=invoice, total_amount=row["total_amount"], tax_amount=row["tax_amount"], discount_amount=row["discount_amount"], due_date=row["due_date"], paid_amount=row["paid_amount"])
        db.add(sale); db.flush()
        db.add(SaleLineModel(sale_id=sale.id, product_id=product.id, quantity=row["quantity"], unit_price=row["unit_price"], cost_price=row["cost_price"]))
        created += 1
    return created
