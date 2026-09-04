from decimal import Decimal

from sqlalchemy import select

from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import SaleModel


def test_persist_sales_stores_discount_and_tax_amounts(db_session, seeder):
    """Regression test for the ingestion pipeline: discount_amount and
    tax_amount used to be hard-coded to 0 in persist_sales() regardless of
    what was in the source file. Confirms real values flow all the way from
    a prepared row through to the stored SaleModel."""
    business = seeder.business()
    rows = [{
        "customer_name": "Acme Traders",
        "product_name": "Widget",
        "invoice_number": "INV-1",
        "transaction_date": "27-08-2026",
        "quantity": "10",
        "unit_price": "100",
        "total_amount": "950",
        "discount_amount": "50",
        "tax": "171",
    }]

    created = persist_sales(db_session, business.id, rows)
    db_session.commit()

    assert created == 1
    sale = db_session.execute(select(SaleModel).where(SaleModel.business_id == business.id)).scalar_one()
    assert sale.discount_amount == Decimal("50")
    assert sale.tax_amount == Decimal("171")


def test_persist_sales_defaults_discount_and_tax_to_zero_when_absent(db_session, seeder):
    business = seeder.business()
    rows = [{
        "customer_name": "Acme Traders",
        "product_name": "Widget",
        "invoice_number": "INV-2",
        "transaction_date": "27-08-2026",
        "quantity": "1",
        "unit_price": "500",
        "total_amount": "500",
    }]

    persist_sales(db_session, business.id, rows)
    db_session.commit()

    sale = db_session.execute(select(SaleModel).where(SaleModel.business_id == business.id)).scalar_one()
    assert sale.discount_amount == Decimal("0")
    assert sale.tax_amount == Decimal("0")


def test_persist_sales_stores_due_date_and_paid_amount(db_session, seeder):
    """Regression test: due_date/paid_amount used to be hard-coded to
    None/0 regardless of what persist_sales() received, which silently
    disabled the entire receivables/overdue-customer feature against real
    ingested data."""
    business = seeder.business()
    rows = [{
        "customer_name": "ABC Electrical",
        "product_name": "MCB 32A",
        "invoice_number": "INV-3",
        "transaction_date": "01-07-2026",
        "quantity": "1",
        "unit_price": "45000",
        "total_amount": "45000",
        "due_date": "31-07-2026",
        "paid_amount": "0",
    }]

    persist_sales(db_session, business.id, rows)
    db_session.commit()

    sale = db_session.execute(select(SaleModel).where(SaleModel.business_id == business.id)).scalar_one()
    assert str(sale.due_date) == "2026-07-31"
    assert sale.paid_amount == Decimal("0")
