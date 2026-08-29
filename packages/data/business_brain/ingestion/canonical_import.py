from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.shared.database.models import CustomerModel, ProductModel, SaleLineModel, SaleModel


def _decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None or str(value).strip() == "":
        return default
    text = str(value).replace("₹", "").replace(",", "").strip()
    text = text.removesuffix("Dr").removesuffix("Cr").strip()
    try:
        return Decimal(text)
    except InvalidOperation:
        return default


def _date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported transaction date: {value}")


def import_sales_rows(db: Session, business_id: UUID, rows: list[dict[str, Any]]) -> dict[str, int]:
    created_sales = created_customers = created_products = created_lines = skipped = 0
    for row in rows:
        invoice = str(row.get("invoice_number") or row.get("voucher_number") or "").strip()
        customer_name = str(row.get("customer_name") or "").strip()
        product_name = str(row.get("product_name") or "").strip()
        if not invoice or not product_name or not row.get("transaction_date"):
            skipped += 1
            continue

        sale = db.scalar(select(SaleModel).where(
            SaleModel.business_id == business_id, SaleModel.invoice_number == invoice
        ))
        if sale is None:
            customer = None
            if customer_name:
                customer = db.scalar(select(CustomerModel).where(
                    CustomerModel.business_id == business_id, CustomerModel.name == customer_name
                ))
                if customer is None:
                    customer = CustomerModel(business_id=business_id, name=customer_name)
                    db.add(customer); db.flush(); created_customers += 1
            sale = SaleModel(
                business_id=business_id,
                customer_id=customer.id if customer else None,
                transaction_date=_date(row["transaction_date"]),
                invoice_number=invoice,
                total_amount=_decimal(row.get("revenue")),
                tax_amount=_decimal(row.get("tax")),
                discount_amount=_decimal(row.get("discount")),
            )
            db.add(sale); db.flush(); created_sales += 1
        else:
            skipped += 1
            continue

        product = db.scalar(select(ProductModel).where(
            ProductModel.business_id == business_id, ProductModel.name == product_name
        ))
        if product is None:
            product = ProductModel(business_id=business_id, name=product_name)
            db.add(product); db.flush(); created_products += 1

        db.add(SaleLineModel(
            sale_id=sale.id,
            product_id=product.id,
            quantity=_decimal(row.get("quantity")),
            unit_price=_decimal(row.get("unit_price")),
            cost_price=_decimal(row.get("cost_price"), default=None),
        ))
        created_lines += 1

    db.commit()
    return {
        "sales_created": created_sales,
        "customers_created": created_customers,
        "products_created": created_products,
        "sale_lines_created": created_lines,
        "rows_skipped": skipped,
    }
