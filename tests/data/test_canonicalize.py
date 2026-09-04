from decimal import Decimal

from packages.data.business_brain.ingestion.canonicalize import canonicalize_sale_row


def _base_row(**overrides) -> dict:
    row = {
        "customer_name": "Acme Traders",
        "product_name": "Widget",
        "invoice_number": "INV-1",
        "transaction_date": "27-08-2026",
        "quantity": "10",
        "unit_price": "100",
        "total_amount": "1000",
    }
    row.update(overrides)
    return row


def test_discount_amount_is_parsed_when_present():
    """Regression test: discount_amount used to be silently dropped here and
    hard-coded to 0 in repository.py, even when the source file had a real
    discount column mapped to it."""
    result = canonicalize_sale_row(_base_row(discount_amount="50"))
    assert result["discount_amount"] == Decimal("50")


def test_discount_amount_defaults_to_zero_when_absent():
    result = canonicalize_sale_row(_base_row())
    assert result["discount_amount"] == Decimal("0")


def test_tax_amount_uses_single_combined_column():
    result = canonicalize_sale_row(_base_row(tax="180"))
    assert result["tax_amount"] == Decimal("180")


def test_tax_amount_sums_split_gst_columns():
    """Tally exports commonly split GST into cgst/sgst (intra-state) or
    just igst (inter-state) rather than one combined column."""
    result = canonicalize_sale_row(_base_row(cgst="45", sgst="45"))
    assert result["tax_amount"] == Decimal("90")


def test_tax_amount_defaults_to_zero_when_absent():
    result = canonicalize_sale_row(_base_row())
    assert result["tax_amount"] == Decimal("0")


def test_due_date_and_paid_amount_are_parsed_when_present():
    """Regression test: due_date and paid_amount used to be dropped here
    entirely (not even in the returned dict), and hard-coded to None/0 in
    repository.py -- which meant overdue_customers()'s `WHERE due_date <
    today` could never match anything on real ingested data, ever."""
    result = canonicalize_sale_row(_base_row(due_date="15-09-2026", paid_amount="600"))
    assert str(result["due_date"]) == "2026-09-15"
    assert result["paid_amount"] == Decimal("600")


def test_due_date_and_paid_amount_default_sensibly_when_absent():
    result = canonicalize_sale_row(_base_row())
    assert result["due_date"] is None
    assert result["paid_amount"] == Decimal("0")


def test_missing_total_amount_raises():
    row = _base_row()
    del row["total_amount"]
    del row["quantity"]
    del row["unit_price"]
    try:
        canonicalize_sale_row(row)
        assert False, "expected ValueError"
    except ValueError:
        pass
