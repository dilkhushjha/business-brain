from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from packages.data.business_brain.normalization.value_parser import parse_date, parse_decimal


def canonicalize_sale_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a prepared source row into database-ready sale fields.

    Sales imports must carry enough line information to support inventory and
    margin reasoning. Missing quantity, price, product or non-positive values
    are rejected rather than guessed.
    """
    parsed_date = parse_date(row.get("transaction_date"))
    if parsed_date is None:
        raise ValueError("transaction_date could not be parsed")

    product_name = _text(row.get("product_name"))
    quantity = parse_decimal(row.get("quantity"))
    unit_price = parse_decimal(row.get("unit_price"))
    total_amount = parse_decimal(row.get("total_amount"))

    if not product_name:
        raise ValueError("product_name is required")
    if quantity is None or quantity <= 0:
        raise ValueError("quantity must be positive")
    if unit_price is None or unit_price < 0:
        raise ValueError("unit_price must be zero or positive")
    if total_amount is None or total_amount <= 0:
        raise ValueError("total_amount must be positive")

    return {
        "customer_name": _text(row.get("customer_name")),
        "product_name": product_name,
        "invoice_number": _text(row.get("invoice_number")),
        "transaction_date": parsed_date,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_amount": total_amount,
        "cost_price": parse_decimal(row.get("cost_price")),
        "discount_amount": parse_decimal(row.get("discount_amount")) or Decimal("0"),
        "tax_amount": _sum_present(row.get("tax"), row.get("cgst"), row.get("sgst"), row.get("igst")),
        "due_date": parse_date(row.get("due_date")),
        "paid_amount": parse_decimal(row.get("paid_amount")) or Decimal("0"),
    }


def canonicalize_purchase_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a prepared purchase row without inventing missing line data."""
    parsed_date = parse_date(row.get("transaction_date"))
    if parsed_date is None:
        raise ValueError("transaction_date could not be parsed")

    product_name = _text(row.get("product_name"))
    quantity = parse_decimal(row.get("quantity"))
    unit_cost = parse_decimal(row.get("unit_price"))
    if unit_cost is None:
        unit_cost = parse_decimal(row.get("cost_price"))
    total_amount = parse_decimal(row.get("total_amount"))

    if not product_name:
        raise ValueError("product_name is required")
    if quantity is None or quantity <= 0:
        raise ValueError("quantity must be positive")
    if unit_cost is None or unit_cost < 0:
        raise ValueError("unit_cost must be zero or positive")
    if total_amount is None or total_amount <= 0:
        raise ValueError("total_amount must be positive")

    return {
        "supplier_name": _text(row.get("supplier_name")),
        "product_name": product_name,
        "invoice_number": _text(row.get("invoice_number")),
        "transaction_date": parsed_date,
        "quantity": quantity,
        "unit_cost": unit_cost,
        "total_amount": total_amount,
        "net_amount": total_amount,
        "discount_amount": parse_decimal(row.get("discount_amount")) or Decimal("0"),
        "tax_amount": _sum_present(row.get("tax"), row.get("cgst"), row.get("sgst"), row.get("igst")),
        "due_date": parse_date(row.get("due_date")),
        "paid_amount": parse_decimal(row.get("paid_amount")) or Decimal("0"),
    }


def canonicalize_expense_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert an expense/payment voucher row into database-ready fields."""
    parsed_date = parse_date(row.get("transaction_date"))
    if parsed_date is None:
        raise ValueError("expense_date could not be parsed")

    amount = parse_decimal(row.get("total_amount"))
    if amount is None or amount <= 0:
        raise ValueError("amount could not be determined or is not positive")

    return {
        "expense_date": parsed_date,
        "category": _text(row.get("category")) or "Uncategorized",
        "amount": amount,
        "description": _text(row.get("description")),
        "external_id": _text(row.get("invoice_number")),
    }


def canonicalize_inventory_snapshot_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a stock summary row into a point-in-time inventory snapshot."""
    parsed_date = parse_date(row.get("transaction_date"))
    if parsed_date is None:
        raise ValueError("snapshot_date could not be parsed")

    quantity = parse_decimal(row.get("closing_qty"))
    if quantity is None:
        quantity = parse_decimal(row.get("quantity"))
    if quantity is None or quantity < 0:
        raise ValueError("closing quantity could not be determined or is negative")

    value = parse_decimal(row.get("closing_value"))
    if value is None:
        value = parse_decimal(row.get("total_amount"))
    if value is None:
        value = Decimal("0")
    if value < 0:
        raise ValueError("closing value cannot be negative")

    return {
        "product_name": _text(row.get("product_name")) or "Unknown product",
        "snapshot_date": parsed_date,
        "quantity": quantity,
        "value": value,
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
