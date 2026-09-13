from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from packages.data.business_brain.ingestion.inventory_repository import persist_inventory_snapshots
from packages.data.business_brain.ingestion.orchestrator import prepare_inventory_file
from packages.shared.database.models import InventorySnapshotModel


def test_stock_summary_csv_with_no_special_columns_is_accepted(db_session, seeder, tmp_path: Path):
    """A real Tally Stock Summary export: one row per item, closing
    quantity/value as of a date -- no invoice number, no customer/supplier
    concept. Confirms prepare_inventory_file() accepts it (unlike
    prepare_file(), which would reject it for missing invoice_number)."""
    business = seeder.business()
    csv_path = tmp_path / "stock_summary.csv"
    csv_path.write_text(
        "Date,Item Name,Closing Qty,Closing Value\n"
        f"{date.today().strftime('%d-%m-%Y')},LED Bulb 9W,20,200\n",
        encoding="utf-8",
    )

    result, prepared = prepare_inventory_file(csv_path)
    assert result.rows_accepted == 1
    assert result.rows_rejected == 0

    created = persist_inventory_snapshots(db_session, business.id, [row.values for row in prepared])
    db_session.commit()

    assert created == 1
    snapshot = db_session.execute(select(InventorySnapshotModel).where(InventorySnapshotModel.business_id == business.id)).scalar_one()
    assert snapshot.quantity == Decimal("20")


def test_csv_stock_summary_produces_a_real_stockout_signal(db_session, seeder, tmp_path: Path):
    """Same proof pattern as every other signal added this session: a real
    Stock Summary CSV, through the actual production ingestion path
    (prepare_inventory_file + persist_inventory_snapshots), into a firing
    STOCKOUT_RISK signal -- not a hand-built fixture."""
    from packages.analytics.business_brain.signals.engine import detect_signals

    business = seeder.business()
    product = seeder.product(business.id, "LED Bulb 9W")
    # Recent sales establish the velocity this product moves at.
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=300, unit_price=10)

    csv_path = tmp_path / "stock_summary.csv"
    csv_path.write_text(
        "Date,Item Name,Closing Qty,Closing Value\n"
        f"{date.today().strftime('%d-%m-%Y')},LED Bulb 9W,20,200\n",
        encoding="utf-8",
    )
    _, prepared = prepare_inventory_file(csv_path)
    persist_inventory_snapshots(db_session, business.id, [row.values for row in prepared])
    db_session.commit()

    signals = detect_signals(db_session, business.id, date.today())
    stockout_signals = [s for s in signals if s.code == "STOCKOUT_RISK"]
    assert len(stockout_signals) == 1
    assert stockout_signals[0].evidence["product"] == "LED Bulb 9W"


def test_stock_summary_csv_would_be_rejected_by_the_sales_shaped_validator(tmp_path: Path):
    """Regression guard: the same file, run through the generic
    prepare_file() instead, should be rejected -- proving
    prepare_inventory_file()'s separate rule set is actually doing
    something, not a no-op duplicate of the expense-file guard."""
    from packages.data.business_brain.ingestion.orchestrator import prepare_file

    csv_path = tmp_path / "stock_summary.csv"
    csv_path.write_text(
        "Date,Item Name,Closing Qty,Closing Value\n"
        "31-08-2026,LED Bulb 9W,20,200\n",
        encoding="utf-8",
    )
    result, prepared = prepare_file(csv_path)
    assert result.rows_rejected == 1
    assert result.rows_accepted == 0
