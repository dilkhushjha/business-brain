from __future__ import annotations

from decimal import Decimal
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
    """Persist canonical sales without committing; caller owns the transaction."""
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
        sale = SaleModel(business_id=business_id, customer_id=customer.id if customer else None, transaction_date=row["transaction_date"], invoice_number=invoice, total_amount=row["total_amount"], tax_amount=Decimal("0"), discount_amount=Decimal("0"))
        db.add(sale); db.flush()
        db.add(SaleLineModel(sale_id=sale.id, product_id=product.id, quantity=row["quantity"], unit_price=row["unit_price"], cost_price=row["cost_price"]))
        created += 1
    return created
