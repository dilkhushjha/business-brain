from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.canonicalize import canonicalize_sale_row
from packages.shared.database.models import CustomerModel, ProductModel, SaleLineModel, SaleModel


def _find_customer(db: Session, business_id: UUID, name: str | None) -> CustomerModel | None:
    if not name:
        return None
    stmt = select(CustomerModel).where(
        CustomerModel.business_id == business_id,
        CustomerModel.name == name,
    )
    return db.execute(stmt).scalar_one_or_none()


def _get_or_create_customer(
    db: Session, business_id: UUID, name: str | None
) -> CustomerModel | None:
    customer = _find_customer(db, business_id, name)
    if customer or not name:
        return customer
    customer = CustomerModel(business_id=business_id, name=name)
    db.add(customer)
    db.flush()
    return customer


def _get_or_create_product(db: Session, business_id: UUID, name: str) -> ProductModel:
    stmt = select(ProductModel).where(
        ProductModel.business_id == business_id,
        ProductModel.name == name,
    )
    product = db.execute(stmt).scalar_one_or_none()
    if product:
        return product
    product = ProductModel(business_id=business_id, name=name)
    db.add(product)
    db.flush()
    return product


def _replace_sale_lines(
    db: Session, sale: SaleModel, rows: list[dict]
) -> None:
    """Replace source-owned lines for an invoice during reconciliation."""
    db.execute(delete(SaleLineModel).where(SaleLineModel.sale_id == sale.id))
    for row in rows:
        product = _get_or_create_product(db, sale.business_id, row["product_name"])
        db.add(
            SaleLineModel(
                sale_id=sale.id,
                product_id=product.id,
                quantity=row["quantity"],
                unit_price=row["unit_price"],
                cost_price=row["cost_price"],
            )
        )


def persist_sales(db: Session, business_id: UUID, rows: list[dict]) -> int:
    """Persist sales as invoice-level records and reconcile repeated exports.

    Tally sales registers commonly contain multiple rows for one invoice.
    The invoice header is therefore created once and every source row becomes
    a SaleLine. When the same invoice is exported again, its source-owned
    header and lines are reconciled instead of silently skipped. The caller
    owns the transaction and decides when to commit/rollback.

    Returns the number of newly-created invoices. Reconciled invoices are not
    counted as new sales, keeping the existing API's ``sales_created`` meaning
    stable while allowing changed payment/due-date values and line items to
    reach the database.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for raw in rows:
        row = canonicalize_sale_row(raw)
        invoice = row["invoice_number"]
        if invoice:
            grouped[invoice].append(row)

    created = 0
    for invoice, invoice_rows in grouped.items():
        header = invoice_rows[0]
        customer = _get_or_create_customer(
            db, business_id, header["customer_name"]
        )
        existing = db.execute(
            select(SaleModel).where(
                SaleModel.business_id == business_id,
                SaleModel.invoice_number == invoice,
            )
        ).scalar_one_or_none()

        if existing:
            existing.customer_id = customer.id if customer else None
            existing.transaction_date = header["transaction_date"]
            existing.total_amount = header["total_amount"]
            existing.tax_amount = header["tax_amount"]
            existing.discount_amount = header["discount_amount"]
            existing.due_date = header["due_date"]
            existing.paid_amount = header["paid_amount"]
            _replace_sale_lines(db, existing, invoice_rows)
            continue

        sale = SaleModel(
            business_id=business_id,
            customer_id=customer.id if customer else None,
            transaction_date=header["transaction_date"],
            invoice_number=invoice,
            total_amount=header["total_amount"],
            tax_amount=header["tax_amount"],
            discount_amount=header["discount_amount"],
            due_date=header["due_date"],
            paid_amount=header["paid_amount"],
        )
        db.add(sale)
        db.flush()
        _replace_sale_lines(db, sale, invoice_rows)
        created += 1

    return created
