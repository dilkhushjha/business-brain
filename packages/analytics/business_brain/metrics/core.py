from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class MetricValue:
    name: str
    value: Decimal
    period: str
    unit: str
    source: str


def gross_margin(revenue: Decimal, cost: Decimal) -> MetricValue:
    margin = Decimal("0") if revenue == 0 else (revenue - cost) / revenue
    return MetricValue("gross_margin", margin, "current", "ratio", "deterministic")


def revenue_growth(current: Decimal, previous: Decimal) -> MetricValue:
    growth = Decimal("0") if previous == 0 else (current - previous) / previous
    return MetricValue("revenue_growth", growth, "current_vs_previous", "ratio", "deterministic")
