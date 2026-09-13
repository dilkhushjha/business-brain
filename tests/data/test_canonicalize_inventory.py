from decimal import Decimal

import pytest

from packages.data.business_brain.ingestion.canonicalize import canonicalize_inventory_snapshot_row


def _base_row(**overrides) -> dict:
    row = {
        "transaction_date": "31-08-2026",
        "product_name": "LED Bulb 9W",
        "closing_qty": "150",
        "closing_value": "9000",
    }
    row.update(overrides)
    return row


def test_basic_snapshot_row_is_parsed():
    result = canonicalize_inventory_snapshot_row(_base_row())
    assert str(result["snapshot_date"]) == "2026-08-31"
    assert result["product_name"] == "LED Bulb 9W"
    assert result["quantity"] == Decimal("150")
    assert result["value"] == Decimal("9000")


def test_falls_back_to_generic_quantity_column():
    row = _base_row()
    del row["closing_qty"]
    row["quantity"] = "80"
    result = canonicalize_inventory_snapshot_row(row)
    assert result["quantity"] == Decimal("80")


def test_value_defaults_to_zero_when_absent():
    row = _base_row()
    del row["closing_value"]
    result = canonicalize_inventory_snapshot_row(row)
    assert result["value"] == Decimal("0")


def test_missing_date_raises():
    row = _base_row()
    del row["transaction_date"]
    with pytest.raises(ValueError):
        canonicalize_inventory_snapshot_row(row)


def test_missing_quantity_raises():
    row = _base_row()
    del row["closing_qty"]
    with pytest.raises(ValueError):
        canonicalize_inventory_snapshot_row(row)


def test_negative_quantity_raises():
    row = _base_row(closing_qty="-5")
    with pytest.raises(ValueError):
        canonicalize_inventory_snapshot_row(row)


def test_zero_quantity_is_valid():
    """A stocked-out item genuinely has zero units on hand -- that's a
    valid, important snapshot, not an error."""
    row = _base_row(closing_qty="0")
    result = canonicalize_inventory_snapshot_row(row)
    assert result["quantity"] == Decimal("0")
