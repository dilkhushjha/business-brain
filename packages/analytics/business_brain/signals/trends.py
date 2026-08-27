from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TrendPoint:
    period: str
    value: Decimal


@dataclass(frozen=True)
class TrendAnalysis:
    direction: str
    strength: Decimal
    consecutive_periods: int
    latest_change: Decimal | None


def analyze_trend(points: list[TrendPoint]) -> TrendAnalysis:
    if len(points) < 2:
        return TrendAnalysis("insufficient_data", Decimal("0"), 0, None)

    changes: list[Decimal] = []
    for previous, current in zip(points, points[1:]):
        if previous.value == 0:
            continue
        changes.append((current.value - previous.value) / abs(previous.value))

    if not changes:
        return TrendAnalysis("flat", Decimal("0"), 0, None)

    direction = "rising" if all(change > 0 for change in changes) else "falling" if all(change < 0 for change in changes) else "mixed"
    consecutive = 0
    if direction in {"rising", "falling"}:
        expected = changes[-1] > 0
        for change in reversed(changes):
            if (change > 0) == expected:
                consecutive += 1
            else:
                break

    strength = sum(abs(change) for change in changes) / Decimal(len(changes))
    return TrendAnalysis(direction, strength, consecutive, changes[-1])
