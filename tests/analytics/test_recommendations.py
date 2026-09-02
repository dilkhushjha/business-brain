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


def _margin_signal(severity: str) -> Signal:
    return Signal(
        code="PRODUCT_MARGIN_DETERIORATION",
        title="LED Bulb 9W has a thin margin",
        severity=severity,
        confidence=Decimal("0.85"),
        metric="gross_margin_pct",
        current_value=Decimal("-4.2"),
        baseline_value=None,
        change=None,
        evidence={"product": "LED Bulb 9W", "revenue": 12000.0, "rule": "margin_pct <= threshold"},
        recommended_next_step="Review pricing or procurement cost for LED Bulb 9W.",
    )


def _receivable_signal(severity: str, days_overdue: int) -> Signal:
    return Signal(
        code="RECEIVABLE_OVERDUE",
        title="ABC Electrical has an overdue payment",
        severity=severity,
        confidence=Decimal("0.95"),
        metric="overdue_amount",
        current_value=Decimal("45000"),
        baseline_value=None,
        change=None,
        evidence={"customer": "ABC Electrical", "days_overdue": days_overdue, "rule": "due_date < today"},
        recommended_next_step="Follow up with ABC Electrical on the overdue payment.",
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


def test_margin_deterioration_produces_review_recommendation():
    recs = generate_recommendations(RecommendationContext(signals=[_margin_signal("critical")], drivers=[]))
    assert len(recs) == 1
    assert recs[0].code == "REVIEW_PRODUCT_MARGIN"
    assert recs[0].priority == "high"
    assert "LED Bulb 9W" in recs[0].title


def test_receivable_overdue_produces_collection_recommendation():
    recs = generate_recommendations(RecommendationContext(signals=[_receivable_signal("critical", 75)], drivers=[]))
    assert len(recs) == 1
    assert recs[0].code == "COLLECT_OVERDUE_RECEIVABLE"
    assert recs[0].priority == "high"
    assert recs[0].evidence["days_overdue"] == 75


def test_mild_receivable_overdue_is_medium_priority():
    recs = generate_recommendations(RecommendationContext(signals=[_receivable_signal("warning", 15)], drivers=[]))
    assert recs[0].priority == "medium"


def test_unknown_signal_code_produces_no_recommendation():
    unknown = _revenue_decline_signal("warning")
    unknown = Signal(**{**unknown.__dict__, "code": "SOME_UNHANDLED_SIGNAL"})
    recs = generate_recommendations(RecommendationContext(signals=[unknown], drivers=[]))
    assert recs == []
