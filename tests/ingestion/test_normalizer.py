from decimal import Decimal

from packages.ingestion.business_brain.ingestion.normalizer import normalize_record


def test_normalize_indian_export_values():
    result = normalize_record(
        {"Bill Date": "27-08-2026", "Party": "ABC", "Qty": "1,200", "Amount": "₹ 45,600.50"},
        {"Bill Date": "date", "Party": "customer", "Qty": "quantity", "Amount": "amount"},
    )
    assert str(result["date"]) == "2026-08-27"
    assert result["customer"] == "ABC"
    assert result["quantity"] == Decimal("1200")
    assert result["amount"] == Decimal("45600.50")
