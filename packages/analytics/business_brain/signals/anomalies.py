from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Anomaly:
    metric: str
    value: Decimal
    baseline: Decimal
    deviation: Decimal
    severity: str
    explanation: str


def percentage_deviation(value: Decimal, baseline: Decimal) -> Decimal | None:
    if baseline == 0:
        return None
    return (value - baseline) / abs(baseline)


def detect_deviation(metric: str, value: Decimal, baseline: Decimal, threshold: Decimal = Decimal("0.30")) -> Anomaly | None:
    deviation = percentage_deviation(value, baseline)
    if deviation is None or abs(deviation) < threshold:
        return None
    severity = "critical" if abs(deviation) >= Decimal("0.50") else "warning"
    direction = "above" if deviation > 0 else "below"
    return Anomaly(
        metric=metric,
        value=value,
        baseline=baseline,
        deviation=deviation,
        severity=severity,
        explanation=f"{metric} is {abs(deviation):.1%} {direction} its baseline.",
    )
