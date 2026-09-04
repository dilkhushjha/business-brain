from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.ingestion.repository import persist_sales
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
