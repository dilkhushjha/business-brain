from decimal import Decimal

from packages.analytics.business_brain.metrics.kpis import KPI
from packages.analytics.business_brain.signals.anomalies import detect_deviation
from packages.analytics.business_brain.signals.rules import (
    detect_customer_decline_signals,
    detect_customer_inactivity_signals,
    detect_kpi_signals,
    detect_margin_signals,
    detect_receivables_signals,
    detect_slow_moving_product_signals,
)
from packages.analytics.business_brain.signals.trends import TrendPoint, analyze_trend


def test_sustained_falling_trend():
    result = analyze_trend([
        TrendPoint("1", Decimal("100")),
        TrendPoint("2", Decimal("90")),
        TrendPoint("3", Decimal("80")),
        TrendPoint("4", Decimal("70")),
    ])
    assert result.direction == "falling"
    assert result.consecutive_periods == 3


def test_mixed_trend():
    result = analyze_trend([
        TrendPoint("1", Decimal("100")),
        TrendPoint("2", Decimal("90")),
        TrendPoint("3", Decimal("95")),
    ])
    assert result.direction == "mixed"


def test_large_baseline_deviation():
    anomaly = detect_deviation("sales", Decimal("150"), Decimal("100"))
    assert anomaly is not None
    assert anomaly.severity == "critical"
    assert anomaly.deviation == Decimal("0.5")


def test_small_deviation_is_ignored():
    assert detect_deviation("sales", Decimal("110"), Decimal("100")) is None


def test_small_kpi_decline_is_not_flagged():
    # Regression test: kpi.change is a percentage (e.g. -5 for -5%), not a
    # 0-1 ratio. A modest 5% dip must not trigger a decline signal.
    kpi = KPI("revenue", Decimal("950"), "INR", "current_month", Decimal("1000"), Decimal("-5"))
    assert detect_kpi_signals([kpi]) == []


def test_material_kpi_decline_is_flagged_with_correct_severity():
    kpi = KPI("revenue", Decimal("700"), "INR", "current_month", Decimal("1000"), Decimal("-30"))
    signals = detect_kpi_signals([kpi])
    assert len(signals) == 1
    assert signals[0].code == "REVENUE_DECLINE"
    assert signals[0].severity == "critical"


def test_kpi_spike_requires_material_change():
    kpi = KPI("revenue", Decimal("1100"), "INR", "current_month", Decimal("1000"), Decimal("10"))
    assert detect_kpi_signals([kpi]) == []


def test_detect_customer_decline_signals():
    rows = [
        {"name": "Acme Traders", "current_revenue": 5000, "previous_revenue": 20000,
         "change_pct": -75.0, "severity": "high"},
        {"name": "Beta Textiles", "current_revenue": 8000, "previous_revenue": 10000,
         "change_pct": -20.0, "severity": "medium"},
    ]
    signals = detect_customer_decline_signals(rows)
    assert len(signals) == 2
    assert signals[0].code == "CUSTOMER_REVENUE_DECLINE"
    assert signals[0].severity == "critical"
    assert signals[0].evidence["customer"] == "Acme Traders"
    assert signals[1].severity == "warning"


def test_detect_margin_signals():
    rows = [
        {"name": "LED Bulb 9W", "revenue": 12000.0, "gross_profit": -500.0, "margin_pct": -4.2, "severity": "high"},
        {"name": "MCB 32A", "revenue": 8000.0, "gross_profit": 400.0, "margin_pct": 5.0, "severity": "medium"},
    ]
    signals = detect_margin_signals(rows)
    assert len(signals) == 2
    assert signals[0].code == "PRODUCT_MARGIN_DETERIORATION"
    assert signals[0].severity == "critical"
    assert signals[0].evidence["product"] == "LED Bulb 9W"
    assert signals[1].severity == "warning"


def test_detect_receivables_signals():
    rows = [
        {"name": "ABC Electrical", "overdue_amount": 45000.0, "days_overdue": 75},
        {"name": "XYZ Traders", "overdue_amount": 6000.0, "days_overdue": 15},
    ]
    signals = detect_receivables_signals(rows)
    assert len(signals) == 2
    assert signals[0].code == "RECEIVABLE_OVERDUE"
    assert signals[0].severity == "critical"
    assert signals[0].evidence["days_overdue"] == 75
    assert signals[1].severity == "warning"


def test_detect_customer_inactivity_signals():
    rows = [
        {"name": "Gone Quiet Ltd", "last_order": "2026-03-01", "inactive_days": 120, "lifetime_revenue": 50000.0},
        {"name": "Slowing Down Co", "last_order": "2026-06-01", "inactive_days": 60, "lifetime_revenue": 8000.0},
    ]
    signals = detect_customer_inactivity_signals(rows)
    assert len(signals) == 2
    assert signals[0].code == "CUSTOMER_INACTIVE"
    assert signals[0].severity == "critical"
    assert signals[0].evidence["customer"] == "Gone Quiet Ltd"
    assert signals[1].severity == "warning"


def test_detect_slow_moving_product_signals():
    rows = [
        {"name": "Winter Jacket", "current_units": 2.0, "previous_units": 20.0, "change_pct": -90.0, "severity": "high"},
        {"name": "Umbrella", "current_units": 6.0, "previous_units": 10.0, "change_pct": -40.0, "severity": "medium"},
    ]
    signals = detect_slow_moving_product_signals(rows)
    assert len(signals) == 2
    assert signals[0].code == "PRODUCT_SLOW_MOVING"
    assert signals[0].severity == "critical"
    assert signals[0].evidence["product"] == "Winter Jacket"
    assert signals[1].severity == "warning"
