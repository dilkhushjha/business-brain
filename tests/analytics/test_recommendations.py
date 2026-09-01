from decimal import Decimal

from packages.analytics.business_brain.recommendations.models import RecommendationContext
from packages.analytics.business_brain.recommendations.rules import generate_recommendations
from packages.analytics.business_brain.signals.models import Signal


def _revenue_decline_signal(severity: str) -> Signal:
    return Signal(
        code="REVENUE_DECLINE",
        title="Revenue is declining",
        severity=severity,
        confidence=Decimal("0.90"),
        metric="revenue",
        current_value=Decimal("700"),
        baseline_value=Decimal("1000"),
        change=Decimal("-30"),
        evidence={"rule": "change <= -10%", "period": "current_month"},
        recommended_next_step="Investigate the drivers of the revenue decline.",
    )


def _customer_decline_signal(severity: str) -> Signal:
    return Signal(
        code="CUSTOMER_REVENUE_DECLINE",
        title="Acme Traders is buying less",
        severity=severity,
        confidence=Decimal("0.95"),
        metric="customer_revenue",
        current_value=Decimal("5000"),
        baseline_value=Decimal("20000"),
        change=Decimal("-75"),
        evidence={"customer": "Acme Traders", "rule": "revenue drop >= threshold vs prior period"},
        recommended_next_step="Reach out to Acme Traders to understand the drop in orders.",
    )


def test_revenue_decline_produces_high_priority_recommendation():
    recs = generate_recommendations(RecommendationContext(signals=[_revenue_decline_signal("critical")], drivers=[]))
    assert len(recs) == 1
    assert recs[0].code == "INVESTIGATE_REVENUE_DECLINE"
    assert recs[0].priority == "high"


def test_customer_decline_produces_retention_recommendation():
    recs = generate_recommendations(RecommendationContext(signals=[_customer_decline_signal("critical")], drivers=[]))
    assert len(recs) == 1
    assert recs[0].code == "RETAIN_DECLINING_CUSTOMER"
    assert recs[0].priority == "high"
    assert "Acme Traders" in recs[0].title
    assert recs[0].evidence["customer"] == "Acme Traders"


def test_mixed_severity_customer_decline_is_medium_priority():
    recs = generate_recommendations(RecommendationContext(signals=[_customer_decline_signal("warning")], drivers=[]))
    assert recs[0].priority == "medium"


def test_unknown_signal_code_produces_no_recommendation():
    unknown = _revenue_decline_signal("warning")
    unknown = Signal(**{**unknown.__dict__, "code": "SOME_UNHANDLED_SIGNAL"})
    recs = generate_recommendations(RecommendationContext(signals=[unknown], drivers=[]))
    assert recs == []
