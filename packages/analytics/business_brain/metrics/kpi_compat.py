from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class KPI:
    name: str
    value: Decimal | None
    unit: str
    period: str
    comparison_value: Decimal | None = None
    change: Decimal | None = None


def _decimal(value: int | float | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def growth(current: int | float | Decimal | None, previous: int | float | Decimal | None) -> Optional[Decimal]:
    current_d = _decimal(current)
    previous_d = _decimal(previous)
    if previous_d == 0:
        return None
    return (current_d - previous_d) / previous_d * Decimal("100")


def average_invoice_value(revenue: int | float | Decimal, invoice_count: int) -> Optional[Decimal]:
    if invoice_count == 0:
        return None
    return _decimal(revenue) / Decimal(invoice_count)
