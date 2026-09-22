from packages.agent.business_brain.agent.responder import render_grounded_response

def test_decision_support_response_uses_prioritized_action():

    context = {
        "evidence": [],
        "signals": [],
        "situations": [{
            "code": "MARGIN_PRESSURE",
            "title": "Procurement costs are putting pressure on margin",
        }],
        "analyses": [],
        "recommendations": [],
        "decision_actions": [{
            "code": "INVESTIGATE_MARGIN_PRESSURE",
            "title": "Investigate procurement-driven margin pressure",
            "priority_level": "immediate",
            "priority_score": "77.0",
            "confidence": "0.90",
            "why_now": "Supplier cost pressure overlaps with margin deterioration.",
            "actions": [
                "Review supplier pricing for affected products.",
                "Compare current selling prices with higher procurement costs.",
            ],
        }],
    }

    answer, confidence = render_grounded_response(
        "What should I do about this?",
        "decision_support",
        context,
    )

    assert confidence == "grounded"
    assert "investigate procurement-driven margin pressure" in answer.lower()
    assert "why now" in answer.lower()
    assert "review supplier pricing" in answer.lower()
