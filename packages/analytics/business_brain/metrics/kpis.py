from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class KPI:
    name: str
    value: Decimal | None
    unit: str
    period: str
    comparison_value: Decimal | None = None
    change: Decimal | None = None


def growth(current: Decimal, previous: Decimal) -> Decimal | None:
    if previous == 0:
        return None
    return (current - previous) / previous


def average_invoice_value(revenue: Decimal, invoice_count: int) -> Decimal | None:
    if invoice_count <= 0:
        return None
    return revenue / Decimal(invoice_count)


def customer_concentration(top_customer_revenue: Decimal, total_revenue: Decimal) -> Decimal | None:
    if total_revenue == 0:
        return None
    return top_customer_revenue / total_revenue
