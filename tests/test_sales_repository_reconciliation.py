from datetime import date
from decimal import Decimal

from sqlalchemy import select

from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import SaleLineModel, SaleModel


def _row(invoice: str, product: str, *, paid: str = "0", total: str = "100") -> dict:
    return {
        "invoice_number": invoice,
        "transaction_date": date.today().isoformat(),
        "customer_name": "Acme Traders",
        "product_name": product,
        "quantity": "1",
        "unit_price": total,
        "total_amount": total,
        "cost_price": "70",
        "discount_amount": "5",
        "tax": "18",
        "due_date": date.today().isoformat(),
        "paid_amount": paid,
    }


def test_multi_line_invoice_is_persisted_once_with_all_lines(db_session, seeder):
    business = seeder.business()
    rows = [_row("INV-100", "Cable"), _row("INV-100", "Switch", total="50")]

    created = persist_sales(db_session, business.id, rows)
    db_session.commit()

    assert created == 1
    sales = db_session.execute(select(SaleModel)).scalars().all()
    lines = db_session.execute(select(SaleLineModel)).scalars().all()
    assert len(sales) == 1
    assert sales[0].invoice_number == "INV-100"
    assert len(lines) == 2


def test_repeated_invoice_export_reconciles_payment_and_lines(db_session, seeder):
    business = seeder.business()
    initial = [_row("INV-200", "Cable", paid="0")]
    assert persist_sales(db_session, business.id, initial) == 1
    db_session.commit()

    updated = [
        _row("INV-200", "Cable", paid="100"),
        _row("INV-200", "Connector", paid="100", total="25"),
    ]
    assert persist_sales(db_session, business.id, updated) == 0
    db_session.commit()

    sale = db_session.execute(select(SaleModel)).scalar_one()
    lines = db_session.execute(select(SaleLineModel)).scalars().all()
    assert sale.paid_amount == Decimal("100")
    assert sale.discount_amount == Decimal("5")
    assert sale.tax_amount == Decimal("18")
    assert len(lines) == 2


def test_reconciliation_is_scoped_to_business(db_session, seeder):
    first = seeder.business("First")
    second = seeder.business("Second")

    assert persist_sales(db_session, first.id, [_row("INV-300", "Cable", paid="10")]) == 1
    assert persist_sales(db_session, second.id, [_row("INV-300", "Cable", paid="90")]) == 1
    db_session.commit()

    sales = db_session.execute(select(SaleModel).order_by(SaleModel.business_id)).scalars().all()
    assert len(sales) == 2
    assert {sale.paid_amount for sale in sales} == {Decimal("10"), Decimal("90")}
