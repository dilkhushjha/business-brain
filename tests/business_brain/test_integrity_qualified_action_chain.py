from decimal import Decimal
from types import SimpleNamespace

from packages.analytics.business_brain.analysis import analyze_situation
from packages.analytics.business_brain.correlations import BusinessSituation
from packages.analytics.business_brain.decision_support import build_decision_actions
from packages.analytics.business_brain.prioritization import prioritize_situations
from packages.analytics.business_brain.qualification import qualify_situations


def test_integrity_qualification_survives_through_action_engine():
    situation = BusinessSituation(
        code="MARGIN_PRESSURE",
        title="Procurement-driven margin pressure",
        severity="warning",
        confidence=Decimal("0.90"),
        signal_codes=["SUPPLIER_PRICE_INCREASE", "PRODUCT_MARGIN_DETERIORATION"],
        evidence={"products": ["HDMI Cable"], "supplier": "Prime Cables"},
        explanation="Supplier cost pressure overlaps with margin deterioration.",
        recommended_next_step="Review supplier pricing.",
    )
    integrity = {
        "status": "attention_required",
        "affected_domains": ["data_quality"],
        "audits": {
            "data_quality": {
                "summary": {"issue_count": 2},
            },
        },
    }

    qualified = qualify_situations([situation], integrity)
    analysis = analyze_situation(qualified[0])
    priority = prioritize_situations(qualified, [analysis])
    actions = build_decision_actions(qualified, priority, [analysis])

    assert qualified[0].confidence == Decimal("0.50")
    assert qualified[0].evidence["integrity_status"] == "attention_required"
    assert qualified[0].evidence["integrity_domains"] == ["data_quality"]
    assert "qualified" in qualified[0].explanation

    assert analysis.situation_code == "MARGIN_PRESSURE"
    assert priority[0].situation_code == "MARGIN_PRESSURE"
    assert actions[0].confidence == Decimal("0.50")
    assert actions[0].evidence["integrity_status"] == "attention_required"
    assert actions[0].title == "Validate data before acting on this situation"
    assert actions[0].actions[0] == (
        "Validate and reconcile the affected data_quality data before acting on this situation."
    )
