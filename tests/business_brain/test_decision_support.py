from decimal import Decimal
from types import SimpleNamespace

from packages.analytics.business_brain.decision_support import build_decision_actions


def test_decision_actions_follow_situation_priority():
    situations = [
        SimpleNamespace(
            code="MARGIN_PRESSURE",
            title="Margin pressure",
            confidence=Decimal("0.90"),
            severity="warning",
            evidence={"products": ["Cable"]},
            recommended_next_step="Review supplier pricing.",
        ),
        SimpleNamespace(
            code="WORKING_CAPITAL_PRESSURE",
            title="Working capital pressure",
            confidence=Decimal("0.80"),
            severity="critical",
            evidence={"overdue_customer_accounts": 2},
            recommended_next_step="Review collections and payables.",
        ),
    ]
    priorities = [
        SimpleNamespace(situation_code="MARGIN_PRESSURE", level="attention", score=Decimal("62")),
        SimpleNamespace(situation_code="WORKING_CAPITAL_PRESSURE", level="immediate", score=Decimal("76")),
    ]
    analyses = [
        SimpleNamespace(situation_code="MARGIN_PRESSURE", impacts=[SimpleNamespace(value=Decimal("8"))]),
        SimpleNamespace(situation_code="WORKING_CAPITAL_PRESSURE", impacts=[]),
    ]

    actions = build_decision_actions(situations, priorities, analyses)

    assert [a.situation_code for a in actions] == [
        "WORKING_CAPITAL_PRESSURE",
        "MARGIN_PRESSURE",
    ]
    assert actions[0].priority_level == "immediate"
    assert actions[0].priority_score == Decimal("76")
    assert actions[1].code == "INVESTIGATE_MARGIN_PRESSURE"


def test_decision_actions_preserve_evidence_and_confidence():
    situation = SimpleNamespace(
        code="MARGIN_PRESSURE",
        title="Margin pressure",
        confidence=Decimal("0.85"),
        severity="warning",
        evidence={"products": ["Cable"], "margin_signals": 1},
        recommended_next_step="Review supplier pricing.",
    )
    priority = SimpleNamespace(
        situation_code="MARGIN_PRESSURE",
        level="attention",
        score=Decimal("60.5"),
    )

    actions = build_decision_actions([situation], [priority], [])

    assert actions[0].evidence == situation.evidence
    assert actions[0].confidence == Decimal("0.85")
    assert actions[0].why_now.startswith("Attention level attention is warranted")
    assert len(actions[0].actions) == 3


def test_qualified_situation_requires_validation_before_action():
    situation = SimpleNamespace(
        code="MARGIN_PRESSURE",
        title="Margin pressure",
        confidence=Decimal("0.50"),
        severity="warning",
        evidence={
            "products": ["Cable"],
            "integrity_status": "attention_required",
            "integrity_domains": ["data_quality"],
        },
        recommended_next_step="Review supplier pricing.",
    )
    priority = SimpleNamespace(
        situation_code="MARGIN_PRESSURE",
        level="attention",
        score=Decimal("49"),
    )

    actions = build_decision_actions([situation], [priority], [])

    assert actions[0].title == "Validate data before acting on this situation"
    assert actions[0].actions[0].startswith("Validate and reconcile")
    assert actions[0].confidence == Decimal("0.50")
