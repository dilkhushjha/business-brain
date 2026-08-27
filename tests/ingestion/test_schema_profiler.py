from packages.ingestion.business_brain.ingestion.field_mapping import suggest_mapping
from packages.ingestion.business_brain.ingestion.schema_profiler import profile_rows


def test_profile_rows():
    profile = profile_rows([
        {"Bill Date": "2026-08-01", "Party Name": "ABC", "Qty": 2},
        {"Bill Date": "2026-08-02", "Party Name": "XYZ", "Qty": None},
    ])
    assert profile.row_count == 2
    assert profile.columns[0].normalized_name == "bill_date"
    assert profile.columns[2].null_ratio == 0.5


def test_suggest_mapping():
    matches = suggest_mapping(["Bill Date", "Party Name", "Qty", "Rate"])
    mapped = {item.source: item.target for item in matches}
    assert mapped["Bill Date"] == "date"
    assert mapped["Party Name"] == "customer"
    assert mapped["Qty"] == "quantity"
    assert mapped["Rate"] == "unit_price"
