from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from packages.data.business_brain.normalization.value_parser import parse_date, parse_decimal


def canonicalize_sale_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a prepared source row into database-ready sale fields."""
    parsed_date = parse_date(row.get("transaction_date"))
    if parsed_date is None:
        raise ValueError("transaction_date could not be parsed")

    quantity = parse_decimal(row.get("quantity"))
    unit_price = parse_decimal(row.get("unit_price"))
    total_amount = parse_decimal(row.get("total_amount"))

    if total_amount is None and quantity is not None and unit_price is not None:
        total_amount = quantity * unit_price

    if total_amount is None:
        raise ValueError("total_amount could not be determined")

    return {
        "customer_name": _text(row.get("customer_name")),
        "product_name": _text(row.get("product_name")) or "Unknown product",
        "invoice_number": _text(row.get("invoice_number")),
        "transaction_date": parsed_date,
        "quantity": quantity or Decimal("1"),
        "unit_price": unit_price or total_amount,
        "total_amount": total_amount,
        "cost_price": parse_decimal(row.get("cost_price")),
        "discount_amount": parse_decimal(row.get("discount_amount")) or Decimal("0"),
        # A Tally export represents tax either as one combined column ("tax")
        # or split across cgst/sgst/igst -- sum whichever are present rather
        # than assuming one particular layout.
        "tax_amount": _sum_present(row.get("tax"), row.get("cgst"), row.get("sgst"), row.get("igst")),
    }


def _sum_present(*values: Any) -> Decimal:
    total = Decimal("0")
    for value in values:
        parsed = parse_decimal(value)
        if parsed is not None:
            total += parsed
    return total


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None
