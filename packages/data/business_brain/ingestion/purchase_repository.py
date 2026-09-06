from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.canonicalize import canonicalize_purchase_row
from packages.shared.database.models import ProductModel, PurchaseLineModel, PurchaseModel, SupplierModel


def _get_or_create_supplier(db: Session, business_id: UUID, name: str | None) -> SupplierModel | None:
    if not name:
        return None
    stmt = select(SupplierModel).where(SupplierModel.business_id == business_id, SupplierModel.name == name)
    supplier = db.execute(stmt).scalar_one_or_none()
    if supplier:
        return supplier
    supplier = SupplierModel(business_id=business_id, name=name)
    db.add(supplier)
    db.flush()
    return supplier


def _get_or_create_product(db: Session, business_id: UUID, name: str) -> ProductModel:
    stmt = select(ProductModel).where(ProductModel.business_id == business_id, ProductModel.name == name)
    product = db.execute(stmt).scalar_one_or_none()
    if product:
        return product
    product = ProductModel(business_id=business_id, name=name)
    db.add(product)
    db.flush()
    return product


def _replace_purchase_lines(db: Session, purchase: PurchaseModel, rows: list[dict]) -> None:
    """Replace source-owned lines for an invoice during reconciliation --
    mirrors _replace_sale_lines in repository.py."""
    db.execute(delete(PurchaseLineModel).where(PurchaseLineModel.purchase_id == purchase.id))
    for row in rows:
        product = _get_or_create_product(db, purchase.business_id, row["product_name"])
        db.add(
            PurchaseLineModel(
                purchase_id=purchase.id,
                product_id=product.id,
                quantity=row["quantity"],
                unit_cost=row["unit_cost"],
                tax_amount=row["tax_amount"],
                discount_amount=row["discount_amount"],
                net_amount=row["net_amount"],
            )
        )


def persist_purchases(db: Session, business_id: UUID, rows: list[dict]) -> int:
    """Persist purchases as invoice-level records and reconcile repeated
    exports. Mirrors persist_sales() in repository.py exactly, on the
    purchase side of the ledger: a Tally purchase register commonly has
    multiple rows per invoice, the invoice header is created once with every
    row becoming a PurchaseLine, and re-exporting the same invoice updates
    it (including due_date/paid_amount) rather than being silently skipped.

    Returns the number of newly-created invoices; reconciled invoices are
    not counted as new.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for raw in rows:
        row = canonicalize_purchase_row(raw)
        invoice = row["invoice_number"]
        if invoice:
            grouped[invoice].append(row)

    created = 0
    for invoice, invoice_rows in grouped.items():
        header = invoice_rows[0]
        supplier = _get_or_create_supplier(db, business_id, header["supplier_name"])
        existing = db.execute(
            select(PurchaseModel).where(
                PurchaseModel.business_id == business_id,
                PurchaseModel.invoice_number == invoice,
            )
        ).scalar_one_or_none()

        if existing:
            existing.supplier_id = supplier.id if supplier else None
            existing.transaction_date = header["transaction_date"]
            existing.total_amount = header["total_amount"]
            existing.tax_amount = header["tax_amount"]
            existing.discount_amount = header["discount_amount"]
            existing.due_date = header["due_date"]
            existing.paid_amount = header["paid_amount"]
            _replace_purchase_lines(db, existing, invoice_rows)
            continue

        purchase = PurchaseModel(
            business_id=business_id,
            supplier_id=supplier.id if supplier else None,
            transaction_date=header["transaction_date"],
            invoice_number=invoice,
            total_amount=header["total_amount"],
            tax_amount=header["tax_amount"],
            discount_amount=header["discount_amount"],
            due_date=header["due_date"],
            paid_amount=header["paid_amount"],
        )
        db.add(purchase)
        db.flush()
        _replace_purchase_lines(db, purchase, invoice_rows)
        created += 1

    return created
