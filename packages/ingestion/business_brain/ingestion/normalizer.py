from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def parse_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return value
    try:
        cleaned = str(value).replace(",", "").replace("₹", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value in (None, ""):
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def normalize_record(record: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for source, target in mapping.items():
        value = record.get(source)
        if target in {"amount", "quantity", "unit_price"}:
            result[target] = parse_decimal(value)
        elif target == "date":
            result[target] = parse_date(value)
        else:
            result[target] = None if value is None else str(value).strip()
    return result
