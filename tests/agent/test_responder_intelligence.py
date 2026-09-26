from packages.agent.business_brain.agent.intent import classify_intent
from packages.agent.business_brain.agent.responder import render_grounded_response


def test_decision_support_answer_contains_priority_confidence_and_evidence():
    question = "What should I do about supplier pricing?"
    context = {
        "decision_actions": [
            {
                "code": "INVESTIGATE_MARGIN_PRESSURE",
                "situation_code": "MARGIN_PRESSURE",
                "title": "Investigate procurement-driven margin pressure",
                "priority_level": "immediate",
                "confidence": "0.85",
                "why_now": "Supplier costs increased while selling prices did not keep pace.",
                "evidence": {"supplier": "Prime Cables", "product": "HDMI Cable 2M"},
                "actions": ["Review supplier pricing.", "Compare selling price."],
            }
        ]
    }

    intent = classify_intent(question)
    answer, confidence = render_grounded_response(question, intent, context)

    assert intent == "decision_support"
    assert confidence == "grounded"
    assert "Priority: immediate" in answer
    assert "Confidence: 85%" in answer
    assert "Prime Cables" in answer
    assert "HDMI Cable 2M" in answer


def test_situation_history_answer_distinguishes_active_and_resolved():
    question = "What changed in my business?"
    context = {
        "situation_history": [
            {"title": "Margin pressure", "status": "active", "trend": "worsening"},
            {"title": "Working capital pressure", "status": "resolved", "trend": "improving"},
        ]
    }

    intent = classify_intent(question)
    answer, confidence = render_grounded_response(question, intent, context)

    assert intent == "situation_history"
    assert confidence == "grounded"
    assert "1 active" in answer
    assert "1 resolved" in answer
    assert "Margin pressure" in answer
    assert "Working capital pressure" in answer
