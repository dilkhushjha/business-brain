from decimal import Decimal

from packages.analytics.business_brain.metrics.kpis import KPI
from packages.analytics.business_brain.signals.models import Signal


# kpi.change is produced by metrics.kpi_compat.growth(), which returns a
# percentage value (e.g. -10 for a 10% decline), not a 0-1 ratio. These
# thresholds must be expressed on the same scale or every non-trivial
# change ends up flagged.
DECLINE_THRESHOLD = Decimal("-10")
SPIKE_THRESHOLD = Decimal("20")


def detect_kpi_signals(kpis: list[KPI]) -> list[Signal]:
    signals: list[Signal] = []
    for kpi in kpis:
        if kpi.change is None:
            continue
        if kpi.change <= DECLINE_THRESHOLD:
            severity = "critical" if kpi.change <= Decimal("-25") else "warning"
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


def detect_customer_decline_signals(declining_customers: list[dict]) -> list[Signal]:
    """Convert declining-customer rows (see metrics.customer_risk.declining_customers)
    into evidence-backed signals so customer risk surfaces in the agent and
    recommendations, not just the dedicated customer-risk endpoints."""
    signals: list[Signal] = []
    for row in declining_customers:
        change_pct = Decimal(str(row["change_pct"]))
        confidence = Decimal("0.95") if row.get("severity") == "high" else Decimal("0.80")
        signals.append(
            Signal(
                code="CUSTOMER_REVENUE_DECLINE",
                title=f"{row['name']} is buying less",
                severity="critical" if row.get("severity") == "high" else "warning",
                confidence=confidence,
                metric="customer_revenue",
                current_value=Decimal(str(row["current_revenue"])),
                baseline_value=Decimal(str(row["previous_revenue"])),
                change=change_pct,
                evidence={"customer": row["name"], "rule": "revenue drop >= threshold vs prior period"},
                recommended_next_step=f"Reach out to {row['name']} to understand the drop in orders.",
            )
        )
    return signals
