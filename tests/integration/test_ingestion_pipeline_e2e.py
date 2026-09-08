from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.shared.database.models import SaleLineModel, SaleModel


def test_csv_with_discount_and_gst_flows_through_to_stored_sale(db_session, seeder, tmp_path: Path):
    """The one 'e2e' pipeline test in this repo (tests/e2e/test_v1_pipeline.py)
    actually exercises packages.ingestion.business_brain (the legacy, unused
    package) rather than packages.data.business_brain.ingestion, which is
    what the real /ingestion/import API route uses. This test exercises the
    real production path: a raw CSV file on disk -> prepare_file() ->
    persist_sales() -> a queryable SaleModel row, including the
    discount/GST columns that used to be silently dropped."""
    business = seeder.business()
    csv_path = tmp_path / "sales_export.csv"
    csv_path.write_text(
        "Bill Date,Party Name,Item Name,Qty,Rate,Net Amount,Discount Amount,CGST,SGST,Invoice No\n"
        "27-08-2026,ABC Electrical,LED Bulb 9W,10,100,950,50,85.5,85.5,INV-001\n",
        encoding="utf-8",
    )

    result, prepared_rows = prepare_file(csv_path)
    assert result.rows_accepted == 1
    assert result.rows_rejected == 0

    created = persist_sales(db_session, business.id, [row.values for row in prepared_rows])
    db_session.commit()

    assert created == 1
    sale = db_session.execute(select(SaleModel).where(SaleModel.business_id == business.id)).scalar_one()
    assert sale.total_amount == Decimal("950")
    assert sale.discount_amount == Decimal("50")
    assert sale.tax_amount == Decimal("171")  # 85.5 CGST + 85.5 SGST

    line = db_session.execute(select(SaleLineModel).where(SaleLineModel.sale_id == sale.id)).scalar_one()
    assert line.quantity == Decimal("10")
    assert line.unit_price == Decimal("100")


def test_csv_with_overdue_invoice_produces_a_real_overdue_signal(db_session, seeder, tmp_path: Path):
    """This is the test that actually proves the receivables fix matters:
    before it, due_date/paid_amount were never set during ingestion, so
    overdue_customers()'s `WHERE due_date < today` could not match ANY row
    ingested through the real pipeline -- the entire receivables feature
    (metric, signal, recommendation) was structurally unreachable from real
    data, only ever exercised in tests via hand-built fixtures. This test
    goes from a raw CSV file with a due date, through the real ingestion
    path, into overdue_customers() and detect_signals(), and confirms the
    overdue invoice is actually found."""
    from packages.analytics.business_brain.metrics.receivables import overdue_customers
    from packages.analytics.business_brain.signals.engine import detect_signals

    business = seeder.business()
    csv_path = tmp_path / "sales_export.csv"
    # due 60 days ago, unpaid -- well past today, using a fixed old invoice
    # date so due_date lands safely in the past regardless of when this runs.
    csv_path.write_text(
        "Bill Date,Party Name,Item Name,Qty,Rate,Net Amount,Due Date,Amount Received,Invoice No\n"
        "01-01-2026,ABC Electrical,MCB 32A,1,45000,45000,01-02-2026,0,INV-OVERDUE-1\n",
        encoding="utf-8",
    )

    _, prepared_rows = prepare_file(csv_path)
    persist_sales(db_session, business.id, [row.values for row in prepared_rows])
    db_session.commit()

    overdue = overdue_customers(db_session, business.id)
    assert len(overdue) == 1
    assert overdue[0]["name"] == "ABC Electrical"
    assert overdue[0]["overdue_amount"] == 45000.0

    from datetime import date
    signals = detect_signals(db_session, business.id, date.today())
    assert any(s.code == "RECEIVABLE_OVERDUE" for s in signals)


def test_purchase_csv_produces_a_real_supplier_price_signal(db_session, seeder, tmp_path: Path):
    """Same shape of proof, on the purchase side: a real purchase-register
    CSV, through prepare_file() + persist_purchases() (the actual
    /ingestion/import-purchases route's logic), into a firing
    SUPPLIER_PRICE_INCREASE signal -- not a hand-built fixture."""
    from packages.analytics.business_brain.signals.engine import detect_signals
    from packages.shared.database.models import PurchaseModel, SupplierModel
    from sqlalchemy import select

    business = seeder.business()

    # Seed the "previous period" purchase directly (outside this CSV import,
    # same as how a real business would have an earlier month's data
    # already in the system) so there's a baseline to compare the new
    # import against.
    product = seeder.product(business.id, "LED Bulb 9W")
    supplier = seeder.supplier(business.id, "ABC Distributors")
    seeder.purchase_with_line(business.id, product.id, supplier_id=supplier.id,
                               days_ago=45, quantity=100, unit_cost=50)

    csv_path = tmp_path / "purchase_export.csv"
    # prepare_file needs a real parseable date -- use today's so the "recent"
    # purchase actually lands in the current 30-day comparison window.
    from datetime import date
    csv_path.write_text(
        "Bill Date,Supplier Name,Item Name,Qty,Rate,Net Amount,Invoice No\n"
        f"{date.today().strftime('%d-%m-%Y')},ABC Distributors,LED Bulb 9W,100,70,7000,PUR-RECENT-1\n",
        encoding="utf-8",
    )

    _, prepared_rows = prepare_file(csv_path)
    persist_purchases(db_session, business.id, [row.values for row in prepared_rows])
    db_session.commit()

    # Confirm the purchase actually landed (not just that the signal fired,
    # in case the signal is somehow satisfied by the seeded baseline alone).
    purchase = db_session.execute(select(PurchaseModel).where(PurchaseModel.invoice_number == "PUR-RECENT-1")).scalar_one()
    assert purchase.total_amount == Decimal("7000")

    signals = detect_signals(db_session, business.id, date.today())
    price_signals = [s for s in signals if s.code == "SUPPLIER_PRICE_INCREASE"]
    assert len(price_signals) == 1
    assert price_signals[0].evidence["supplier"] == "ABC Distributors"


def test_csv_with_outlier_discount_produces_a_real_discount_anomaly_signal(db_session, seeder, tmp_path: Path):
    """A real CSV file with a large discount column, through the real
    ingestion path, into a firing DISCOUNT_ANOMALY signal -- same proof
    pattern as the receivables/supplier-price end-to-end tests: not just
    that discount_amount lands in the database, but that the whole chain
    from file to signal actually works."""
    from datetime import date

    from packages.analytics.business_brain.signals.engine import detect_signals

    business = seeder.business()
    customer = seeder.customer(business.id, "Regular Buyer")
    outlier = seeder.customer(business.id, "Big Discount Customer")

    # Baseline: a consistent ~5% discount rate across several invoices.
    for _ in range(4):
        seeder.sale(business.id, customer_id=customer.id, days_ago=10,
                    total_amount=Decimal("950"), discount_amount=Decimal("50"))

    csv_path = tmp_path / "outlier_sale.csv"
    csv_path.write_text(
        "Bill Date,Party Name,Item Name,Qty,Rate,Net Amount,Discount Amount,Invoice No\n"
        f"{date.today().strftime('%d-%m-%Y')},Big Discount Customer,Widget,1,600,600,400,INV-OUTLIER-1\n",
        encoding="utf-8",
    )
    _, prepared_rows = prepare_file(csv_path)
    persist_sales(db_session, business.id, [row.values for row in prepared_rows])
    db_session.commit()

    signals = detect_signals(db_session, business.id, date.today())
    discount_signals = [s for s in signals if s.code == "DISCOUNT_ANOMALY"]
    assert len(discount_signals) == 1
    assert discount_signals[0].evidence["customer"] == "Big Discount Customer"
