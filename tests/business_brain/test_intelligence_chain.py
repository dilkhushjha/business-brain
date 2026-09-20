from decimal import Decimal
from types import SimpleNamespace

from packages.agent.business_brain.agent.responder import render_grounded_response
from packages.analytics.business_brain.correlations import correlate_signals
from packages.analytics.business_brain.recommendations.models import RecommendationContext
from packages.analytics.business_brain.recommendations.rules import generate_recommendations


def signal(code, severity="warning", evidence=None, confidence="0.85"):
    return SimpleNamespace(
        code=code,
        severity=severity,
        evidence=evidence or {},
        confidence=Decimal(confidence),
        change=None,
        current_value=None,
    )


def test_situation_to_recommendation_chain():
    signals = [
        signal("SUPPLIER_PRICE_INCREASE", evidence={"supplier": "Supplier A", "product": "Cable"}),
        signal("PRODUCT_MARGIN_DETERIORATION", evidence={"product": "Cable"}),
    ]

    situations = correlate_signals(signals)
    recommendations = generate_recommendations(
        RecommendationContext(signals=signals, drivers=situations)
    )

    assert [s.code for s in situations] == ["MARGIN_PRESSURE"]
    assert [r.code for r in recommendations] == [
        "INVESTIGATE_MARGIN_PRESSURE",
        "REVIEW_PRODUCT_MARGIN",
        "REVIEW_SUPPLIER_PRICE_INCREASE",
    ]
    assert recommendations[0].evidence == situations[0].evidence
    assert recommendations[0].confidence == situations[0].confidence


def test_situation_is_visible_in_grounded_agent_response():
    signals = [
        signal("SUPPLIER_PRICE_INCREASE", evidence={"supplier": "Supplier A", "product": "Cable"}),
        signal("PRODUCT_MARGIN_DETERIORATION", evidence={"product": "Cable"}),
    ]
    situations = correlate_signals(signals)

    context = {
        "evidence": [{
            "metric": "gross_margin_pct",
            "value": "8.0",
            "metadata": {"revenue": "10000", "cost": "9200"},
        }],
        "signals": [vars(s) for s in signals],
        "situations": [vars(s) for s in situations],
        "recommendations": [],
    }

    answer, confidence = render_grounded_response(
        "Why is my margin under pressure?",
        "margin_analysis",
        context,
    )

    assert confidence == "grounded"
    assert "procurement costs are putting pressure on margin" in answer.lower()
    assert "cross-domain business situation" in answer.lower()


def test_no_evidence_does_not_produce_a_grounded_agent_answer():
    answer, confidence = render_grounded_response(
        "How is my business doing?",
        "business_health",
        {"evidence": [], "signals": [], "situations": [], "recommendations": []},
    )

    assert confidence == "insufficient_evidence"
    assert "enough sales evidence" in answer.lower()


def test_unrelated_signals_do_not_create_downstream_recommendation():
    signals = [
        signal("CUSTOMER_INACTIVE", evidence={"customer": "Customer A"}),
        signal("EXPENSE_SPIKE", evidence={"category": "Rent"}),
    ]

    situations = correlate_signals(signals)
    recommendations = generate_recommendations(
        RecommendationContext(signals=[], drivers=situations)
    )

    assert situations == []
    assert recommendations == []


def test_recommendation_preserves_situation_confidence_and_evidence():
    signals = [
        signal("RECEIVABLE_OVERDUE", severity="critical", evidence={"customer": "Customer A"}),
        signal("PAYABLE_OVERDUE", evidence={"supplier": "Supplier A"}),
    ]

    situations = correlate_signals(signals)
    recommendations = generate_recommendations(
        RecommendationContext(signals=signals, drivers=situations)
    )

    assert len(situations) == 1
    assert situations[0].code == "WORKING_CAPITAL_PRESSURE"
    assert recommendations[0].code == "REVIEW_WORKING_CAPITAL_PRESSURE"
    assert recommendations[0].priority == "high"
    assert recommendations[0].confidence == Decimal("0.86")
    assert recommendations[0].evidence == situations[0].evidence
