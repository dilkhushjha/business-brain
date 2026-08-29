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


def growth(current: Decimal, previous: Decimal) -> Optional[Decimal]:
    if previous == 0:
        return None
    return (current - previous) / previous * Decimal("100")


def average_invoice_value(revenue: Decimal, invoice_count: int) -> Optional[Decimal]:
    if invoice_count == 0:
        return None
    return revenue / Decimal(invoice_count)
