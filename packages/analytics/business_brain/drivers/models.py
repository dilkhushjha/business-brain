from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DriverContribution:
    dimension: str
    key: str
    label: str
    current_value: Decimal
    baseline_value: Decimal
    change: Decimal
    contribution: Decimal


@dataclass(frozen=True)
class DriverAnalysis:
    metric: str
    current_value: Decimal
    baseline_value: Decimal
    delta: Decimal
    drivers: list[DriverContribution]
