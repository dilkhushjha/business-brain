from decimal import Decimal

from packages.analytics.business_brain.metrics.kpis import KPI
from packages.analytics.business_brain.signals.models import Signal


DECLINE_THRESHOLD = Decimal("-0.10")
SPIKE_THRESHOLD = Decimal("0.20")


def detect_kpi_signals(kpis: list[KPI]) -> list[Signal]:
    signals: list[Signal] = []
    for kpi in kpis:
        if kpi.change is None:
            continue
        if kpi.change <= DECLINE_THRESHOLD:
            severity = "critical" if kpi.change <= Decimal("-0.25") else "warning"
            signals.append(
                Signal(
                    code=f"{kpi.name.upper()}_DECLINE",
                    title=f"{kpi.name.replace('_', ' ').title()} is declining",
                    severity=severity,
                    confidence=Decimal("0.90"),
                    metric=kpi.name,
                    current_value=kpi.value,
                    baseline_value=kpi.comparison_value,
                    change=kpi.change,
                    evidence={"rule": "change <= -10%", "period": kpi.period},
                    recommended_next_step=f"Investigate the drivers of the {kpi.name.replace('_', ' ')} decline.",
                )
            )
        elif kpi.change >= SPIKE_THRESHOLD:
            signals.append(
                Signal(
                    code=f"{kpi.name.upper()}_SPIKE",
                    title=f"{kpi.name.replace('_', ' ').title()} is rising unusually fast",
                    severity="info",
                    confidence=Decimal("0.85"),
                    metric=kpi.name,
                    current_value=kpi.value,
                    baseline_value=kpi.comparison_value,
                    change=kpi.change,
                    evidence={"rule": "change >= +20%", "period": kpi.period},
                    recommended_next_step=f"Check which products, customers or categories are driving the {kpi.name.replace('_', ' ')} increase.",
                )
            )
    return signals
