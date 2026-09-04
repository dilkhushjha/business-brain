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


def detect_margin_signals(low_margin_products: list[dict]) -> list[Signal]:
    """Convert low-margin-product rows (see metrics.margin.low_margin_products)
    into evidence-backed signals so margin erosion surfaces in the agent and
    recommendations, not just the dedicated margin endpoint."""
    signals: list[Signal] = []
    for row in low_margin_products:
        signals.append(
            Signal(
                code="PRODUCT_MARGIN_DETERIORATION",
                title=f"{row['name']} has a thin margin",
                severity="critical" if row.get("severity") == "high" else "warning",
                confidence=Decimal("0.85"),
                metric="gross_margin_pct",
                current_value=Decimal(str(row["margin_pct"])),
                baseline_value=None,
                change=None,
                evidence={"product": row["name"], "revenue": row["revenue"], "rule": "margin_pct <= threshold"},
                recommended_next_step=f"Review pricing or procurement cost for {row['name']}.",
            )
        )
    return signals


def detect_receivables_signals(overdue_customers: list[dict]) -> list[Signal]:
    """Convert overdue-customer rows (see metrics.receivables.overdue_customers)
    into evidence-backed signals so receivable risk surfaces in the agent and
    recommendations, not just the dedicated receivables endpoint."""
    signals: list[Signal] = []
    for row in overdue_customers:
        days_overdue = row["days_overdue"]
        severity = "critical" if days_overdue > 60 else "warning"
        confidence = Decimal("0.95") if days_overdue > 60 else Decimal("0.85")
        signals.append(
            Signal(
                code="RECEIVABLE_OVERDUE",
                title=f"{row['name']} has an overdue payment",
                severity=severity,
                confidence=confidence,
                metric="overdue_amount",
                current_value=Decimal(str(row["overdue_amount"])),
                baseline_value=None,
                change=None,
                evidence={"customer": row["name"], "days_overdue": days_overdue, "rule": "due_date < today"},
                recommended_next_step=f"Follow up with {row['name']} on the overdue payment ({days_overdue} days overdue).",
            )
        )
    return signals


def detect_customer_inactivity_signals(inactive_customers: list[dict]) -> list[Signal]:
    """Convert inactive-customer rows (see metrics.customer_risk.inactive_customers)
    into evidence-backed signals. Distinct from CUSTOMER_REVENUE_DECLINE: this
    fires for customers who have gone quiet entirely (no orders at all in the
    window), not ones who are still buying but less."""
    signals: list[Signal] = []
    for row in inactive_customers:
        inactive_days = row["inactive_days"]
        severity = "critical" if inactive_days and inactive_days > 90 else "warning"
        confidence = Decimal("0.90") if inactive_days and inactive_days > 90 else Decimal("0.75")
        signals.append(
            Signal(
                code="CUSTOMER_INACTIVE",
                title=f"{row['name']} has gone quiet",
                severity=severity,
                confidence=confidence,
                metric="days_since_last_order",
                current_value=Decimal(str(inactive_days)) if inactive_days is not None else None,
                baseline_value=None,
                change=None,
                evidence={
                    "customer": row["name"], "last_order": row.get("last_order"),
                    "lifetime_revenue": row.get("lifetime_revenue"),
                    "rule": "no order in inactive_days window",
                },
                recommended_next_step=f"Check in with {row['name']} -- no orders in {inactive_days} days.",
            )
        )
    return signals


def detect_slow_moving_product_signals(slow_moving_products: list[dict]) -> list[Signal]:
    """Convert slow-moving-product rows (see metrics.inventory.slow_moving_products)
    into evidence-backed signals. Approximates 'slow-moving inventory' from a
    material drop in sales velocity, since there's no stock-on-hand data in
    this schema to compute true days-of-inventory-remaining."""
    signals: list[Signal] = []
    for row in slow_moving_products:
        change_pct = Decimal(str(row["change_pct"]))
        confidence = Decimal("0.85") if row.get("severity") == "high" else Decimal("0.70")
        signals.append(
            Signal(
                code="PRODUCT_SLOW_MOVING",
                title=f"{row['name']} is selling much slower",
                severity="critical" if row.get("severity") == "high" else "warning",
                confidence=confidence,
                metric="units_sold",
                current_value=Decimal(str(row["current_units"])),
                baseline_value=Decimal(str(row["previous_units"])),
                change=change_pct,
                evidence={"product": row["name"], "rule": "sales velocity drop >= threshold vs prior period"},
                recommended_next_step=f"Review pricing, promotion or reorder quantity for {row['name']}.",
            )
        )
    return signals
