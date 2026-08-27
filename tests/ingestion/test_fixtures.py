import csv
from pathlib import Path

from packages.ingestion.business_brain.ingestion.field_mapping import suggest_mapping
from packages.ingestion.business_brain.ingestion.schema_profiler import profile_rows


FIXTURES = Path(__file__).parents[1] / "fixtures"


def _read(name):
    with (FIXTURES / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_electrical_fixture_profiles_and_maps():
    rows = _read("electrical_sales_messy.csv")
    profile = profile_rows(rows)
    assert profile.row_count == 10
    mapped = {m.source: m.target for m in suggest_mapping([c.name for c in profile.columns])}
    assert mapped["Bill Date"] == "date"
    assert mapped["Party Name"] == "customer"
    assert mapped["Stock Item"] == "product"
    assert mapped["Qty"] == "quantity"
    assert mapped["Rate"] == "unit_price"
    assert mapped["Net Amount"] == "amount"


def test_retail_fixture_profiles_and_maps():
    rows = _read("retail_sales_messy.csv")
    profile = profile_rows(rows)
    assert profile.row_count == 8
    mapped = {m.source: m.target for m in suggest_mapping([c.name for c in profile.columns])}
    assert mapped["Bill Date"] == "date"
    assert mapped["Item"] == "product"
    assert mapped["Qty"] == "quantity"
    assert mapped["Rate"] == "unit_price"
    assert mapped["Amount"] == "amount"
