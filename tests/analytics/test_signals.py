from decimal import Decimal

from packages.analytics.business_brain.signals.anomalies import detect_deviation
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
