from decimal import Decimal
from packages.agent.business_brain.agent.intent import classify_intent
from packages.agent.business_brain.agent.responder import render_grounded_response


def test_executive_attention_questions_route_to_decision_support():
    questions = [
        "What needs my attention?",
        "What should I focus on?",
        "What is the biggest issue in my business?",
        "What should I pay attention to?",
    ]

    assert all(classify_intent(question) == "decision_support" for question in questions)


def test_general_business_question_produces_executive_summary():
    context = {
        "evidence": [
            {"metric": "revenue", "value": "12500", "metadata": {}},
            {"metric": "gross_margin_pct", "value": "18.5", "metadata": {}},
        ],
        "signals": [],
        "situations": [
            {"code": "MARGIN_PRESSURE", "title": "Procurement-driven margin pressure"}
        ],
        "decision_actions": [
            {"code": "INVESTIGATE_MARGIN_PRESSURE", "title": "Investigate procurement-driven margin pressure"}
        ],
    }

    answer, confidence = render_grounded_response(
        "Give me a quick overview",
        "general_business",
        context,
    )

    assert confidence == "grounded"
    assert "₹12,500.00" in answer
    assert "18.5%" in answer
    assert "procurement-driven margin pressure" in answer.lower()
    assert "suggested next step" in answer.lower()


def test_general_business_without_evidence_remains_provisional():
    answer, confidence = render_grounded_response(
        "Give me a quick overview",
        "general_business",
        {"evidence": [], "signals": [], "situations": [], "decision_actions": []},
    )

    assert confidence == "insufficient_evidence"
    assert "enough business evidence" in answer.lower()
