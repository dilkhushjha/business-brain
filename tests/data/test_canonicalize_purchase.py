from decimal import Decimal

from packages.data.business_brain.ingestion.canonicalize import canonicalize_purchase_row


def _base_row(**overrides) -> dict:
    row = {
        "supplier_name": "ABC Distributors",
        "product_name": "LED Bulb 9W",
        "invoice_number": "PUR-1",
        "transaction_date": "27-08-2026",
        "quantity": "100",
        "unit_price": "60",
        "total_amount": "6000",
    }
    row.update(overrides)
    return row


def test_unit_price_column_becomes_unit_cost():
    """A purchase register's 'Rate' column maps to the same generic
    unit_price canonical field a sales register uses -- canonicalize_purchase_row
    relabels it to unit_cost since that's PurchaseLineModel's actual column."""
    result = canonicalize_purchase_row(_base_row())
    assert result["unit_cost"] == Decimal("60")
    assert result["total_amount"] == Decimal("6000")
    assert result["net_amount"] == Decimal("6000")


def test_falls_back_to_cost_price_column_if_unit_price_absent():
    row = _base_row()
    del row["unit_price"]
    row["cost_price"] = "55"
    result = canonicalize_purchase_row(row)
    assert result["unit_cost"] == Decimal("55")


def test_discount_and_tax_are_parsed():
    result = canonicalize_purchase_row(_base_row(discount_amount="200", tax="540"))
    assert result["discount_amount"] == Decimal("200")
    assert result["tax_amount"] == Decimal("540")


def test_discount_and_tax_default_to_zero_when_absent():
    result = canonicalize_purchase_row(_base_row())
    assert result["discount_amount"] == Decimal("0")
    assert result["tax_amount"] == Decimal("0")


def test_due_date_and_paid_amount_are_parsed():
    result = canonicalize_purchase_row(_base_row(due_date="30-09-2026", paid_amount="3000"))
    assert str(result["due_date"]) == "2026-09-30"
    assert result["paid_amount"] == Decimal("3000")


def test_missing_total_amount_raises():
    row = _base_row()
    del row["total_amount"]
    del row["quantity"]
    del row["unit_price"]
    try:
        canonicalize_purchase_row(row)
        assert False, "expected ValueError"
    except ValueError:
        pass
