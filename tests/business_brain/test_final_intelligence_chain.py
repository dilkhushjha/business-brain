from decimal import Decimal
from types import SimpleNamespace

from packages.analytics.business_brain.analysis import analyze_situation
from packages.analytics.business_brain.decision_support import build_decision_actions
from packages.analytics.business_brain.prioritization import prioritize_situations
from packages.analytics.business_brain.state import BusinessState


def test_full_business_brain_reasoning_chain():
    situation = SimpleNamespace(
        code="MARGIN_PRESSURE",
        title="Margin pressure",
        severity="warning",
        confidence=Decimal("0.90"),
        signal_codes=["SUPPLIER_PRICE_INCREASE", "PRODUCT_MARGIN_DETERIORATION"],
        evidence={
            "affected_products": ["Cable"],
            "supplier": "Supplier A",
            "supplier_price_change": "12",
        },
        explanation="Supplier cost pressure overlaps with product margin deterioration.",
        recommended_next_step="Review supplier pricing and selling price.",
    )
    state = BusinessState(
        revenue=Decimal("10000"),
        gross_profit=Decimal("1200"),
        gross_margin_pct=Decimal("12"),
        purchase_spend=Decimal("5000"),
        total_expenses=Decimal("700"),
    )

    analysis = analyze_situation(situation, state)
    priority = prioritize_situations([situation], [analysis])[0]
    actions = build_decision_actions(
        [situation],
        [priority],
        [analysis],
        [],
    )

    assert analysis.situation_code == "MARGIN_PRESSURE"
    assert analysis.root_causes
    assert analysis.impacts
    assert priority.situation_code == "MARGIN_PRESSURE"
    assert priority.score > 0
    assert actions[0].situation_code == "MARGIN_PRESSURE"
    assert actions[0].priority_score == priority.score
    assert actions[0].confidence == situation.confidence
    assert actions[0].evidence == situation.evidence
    assert actions[0].actions
