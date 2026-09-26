from packages.agent.business_brain.agent.intent import classify_intent
from packages.agent.business_brain.agent.responder import render_grounded_response


def _action(code="INVESTIGATE_MARGIN_PRESSURE"):
    return {
        "code": code,
        "situation_code": "MARGIN_PRESSURE",
        "title": "Investigate procurement-driven margin pressure",
        "priority_level": "attention",
        "confidence": "0.65",
        "why_now": "Supplier costs and selling margins overlap on the same product.",
        "actions": [
            "Review supplier pricing for affected products.",
            "Compare current selling prices with higher procurement costs.",
        ],
    }


def test_intent_classifier_prioritizes_decision_questions():
    assert classify_intent("What should I do about my margin?") == "decision_support"
    assert classify_intent("What should I do about supplier pricing?") == "decision_support"
    assert classify_intent("Why is my margin low?") == "root_cause"
    assert classify_intent("What is my gross margin?") == "margin_analysis"


def test_decision_response_uses_grounded_action():
    answer, confidence = render_grounded_response(
        "What should I do about my margin?",
        "decision_support",
        {"decision_actions": [_action()]},
    )

    assert confidence == "grounded"
    assert "Investigate procurement-driven margin pressure" in answer
    assert "Why now:" in answer
    assert "Review supplier pricing" in answer


def test_data_integrity_response_is_explicit_about_uncertainty():
    answer, confidence = render_grounded_response(
        "Can I trust the data?",
        "data_integrity",
        {
            "integrity": {
                "status": "attention_required",
                "issue_count": 3,
                "affected_domains": ["data_quality", "inventory"],
            }
        },
    )

    assert confidence == "grounded"
    assert "3 integrity issue(s)" in answer
    assert "data_quality, inventory" in answer


def test_root_cause_response_does_not_claim_proven_causality():
    answer, confidence = render_grounded_response(
        "What caused the margin problem?",
        "root_cause",
        {
            "analyses": [{
                "situation_code": "MARGIN_PRESSURE",
                "root_causes": [{
                    "title": "Supplier cost increase",
                    "evidence": {"products": ["HDMI Cable 2M"]},
                }],
                "impacts": [{
                    "description": "Gross margin is under pressure.",
                }],
            }]
        },
    )

    assert confidence == "grounded"
    assert "can't call this a proven single cause" in answer
    assert "Supplier cost increase" in answer
    assert "HDMI Cable 2M" in answer


def test_empty_context_returns_insufficient_evidence():
    answer, confidence = render_grounded_response(
        "How is my business doing?",
        "business_health",
        {},
    )

    assert confidence == "insufficient_evidence"
    assert "enough sales evidence" in answer
