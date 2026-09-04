from decimal import Decimal

from packages.data.business_brain.normalization.column_mapper import suggest_mapping
from packages.data.business_brain.normalization.value_parser import parse_date, parse_decimal
from packages.data.business_brain.validation.schema import FieldRule, validate_row


def test_column_alias_mapping():
    result = suggest_mapping(["Party Name", "Qty", "Invoice No", "Bill Date"])
    mapped = {item.source_column: item.canonical_field for item in result}
    assert mapped["Party Name"] == "customer_name"
    assert mapped["Qty"] == "quantity"
    assert mapped["Invoice No"] == "invoice_number"


def test_discount_column_is_recognized():
    result = suggest_mapping(["Discount Amount"])
    mapped = {item.source_column: item.canonical_field for item in result}
    assert mapped["Discount Amount"] == "discount_amount"


def test_due_date_and_paid_amount_columns_are_recognized():
    result = suggest_mapping(["Due Date", "Amount Received"])
    mapped = {item.source_column: item.canonical_field for item in result}
    assert mapped["Due Date"] == "due_date"
    assert mapped["Amount Received"] == "paid_amount"
    # Confirm "Due Date" doesn't get misassigned to transaction_date's "date" alias.
    assert mapped["Due Date"] != "transaction_date"


def test_parse_indian_number_format():
    assert parse_decimal("₹1,25,000.50") == Decimal("125000.50")


def test_parse_common_date_formats():
    assert str(parse_date("27/08/2026")) == "2026-08-27"


def test_required_and_numeric_validation():
    issues = validate_row(
        {"customer_name": "", "quantity": "ten"},
        [FieldRule("customer_name", required=True), FieldRule("quantity", kind="number")],
        7,
    )
    assert {issue.code for issue in issues} == {"REQUIRED", "INVALID_NUMBER"}
