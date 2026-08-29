from pathlib import Path

import pytest

from packages.data.business_brain.ingestion.orchestrator import prepare_file


FIXTURE = Path(__file__).parent / "fixtures" / "tally_sales_sample.csv"


def test_tally_fixture_is_profiled_and_cleaned():
    result, prepared = prepare_file(str(FIXTURE), source_name=FIXTURE.name)

    assert result.rows_read == 3
    assert result.rows_accepted == 3
    assert result.rows_rejected == 0
    assert len(prepared) == 3


def test_tally_fixture_preserves_business_fields():
    _, prepared = prepare_file(str(FIXTURE), source_name=FIXTURE.name)
    rows = [row.values for row in prepared]

    assert {row.get("voucher_number") for row in rows} == {"INV-001", "INV-002", "INV-003"}
    assert rows[0].get("customer_name") == "ABC Electricals"
    assert rows[0].get("product_name") == "Copper Cable"
    assert str(rows[0].get("revenue")) in {"5000", "5000.0", "5000.00"}
