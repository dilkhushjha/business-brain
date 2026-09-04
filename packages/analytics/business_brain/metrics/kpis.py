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


def growth(current: int | float | Decimal | None, previous: int | float | Decimal | None) -> Optional[Decimal]:
    current_d = _as_decimal(current)
    previous_d = _as_decimal(previous)
    if previous_d == 0:
        return None
    return (current_d - previous_d) / previous_d * Decimal("100")


def average_invoice_value(revenue: int | float | Decimal, invoice_count: int) -> Optional[Decimal]:
    if invoice_count == 0:
        return None
    return _as_decimal(revenue) / Decimal(invoice_count)


def customer_concentration(customer_revenue: Decimal, total_revenue: Decimal) -> Optional[Decimal]:
    """Return a customer's share of total revenue as a ratio (0-1), not a
    percentage. Distinct from metrics.customer_risk.customer_concentration,
    which returns a richer dict (top customers, risk banding) for the
    /customer-concentration API route -- this is a standalone utility."""
    if total_revenue == 0:
        return None
    return customer_revenue / total_revenue


def _as_decimal(value: int | float | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
