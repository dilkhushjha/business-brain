from decimal import Decimal

from packages.analytics.business_brain.drivers.models import DriverAnalysis, DriverContribution


def rank_drivers(
    metric: str,
    current_total: Decimal,
    baseline_total: Decimal,
    current_by_dimension: dict[str, Decimal],
    baseline_by_dimension: dict[str, Decimal],
    dimension: str,
    limit: int = 10,
) -> DriverAnalysis:
    keys = set(current_by_dimension) | set(baseline_by_dimension)
    delta = current_total - baseline_total
    drivers: list[DriverContribution] = []
    for key in keys:
        current = current_by_dimension.get(key, Decimal("0"))
        baseline = baseline_by_dimension.get(key, Decimal("0"))
        contribution = current - baseline
        drivers.append(
            DriverContribution(
                dimension=dimension,
                key=key,
                label=key,
                current_value=current,
                baseline_value=baseline,
                change=(contribution / abs(baseline)) if baseline else Decimal("0"),
                contribution=contribution,
            )
        )
    drivers.sort(key=lambda item: abs(item.contribution), reverse=True)
    return DriverAnalysis(metric, current_total, baseline_total, delta, drivers[:limit])
