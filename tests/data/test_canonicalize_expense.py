from decimal import Decimal

import pytest

from packages.data.business_brain.ingestion.canonicalize import canonicalize_expense_row


def _base_row(**overrides) -> dict:
    row = {
        "transaction_date": "05-08-2026",
        "category": "Rent",
        "total_amount": "25000",
        "description": "August shop rent",
    }
    row.update(overrides)
    return row


def test_basic_expense_row_is_parsed():
    result = canonicalize_expense_row(_base_row())
    assert str(result["expense_date"]) == "2026-08-05"
    assert result["category"] == "Rent"
    assert result["amount"] == Decimal("25000")
    assert result["description"] == "August shop rent"
    assert result["external_id"] is None


def test_voucher_number_becomes_external_id():
    result = canonicalize_expense_row(_base_row(invoice_number="EXP-0042"))
    assert result["external_id"] == "EXP-0042"


def test_category_defaults_to_uncategorized_when_absent():
    row = _base_row()
    del row["category"]
    result = canonicalize_expense_row(row)
    assert result["category"] == "Uncategorized"


def test_missing_date_raises():
    row = _base_row()
    del row["transaction_date"]
    with pytest.raises(ValueError):
        canonicalize_expense_row(row)


def test_missing_amount_raises():
    row = _base_row()
    del row["total_amount"]
    with pytest.raises(ValueError):
        canonicalize_expense_row(row)


def test_zero_amount_raises():
    row = _base_row(total_amount="0")
    with pytest.raises(ValueError):
        canonicalize_expense_row(row)


def test_negative_amount_raises():
    row = _base_row(total_amount="-100")
    with pytest.raises(ValueError):
        canonicalize_expense_row(row)
