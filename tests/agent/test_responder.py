from packages.agent.business_brain.agent.responder import render_grounded_response


def test_business_health_with_evidence_is_grounded():
    context = {"evidence": [{"metric": "revenue", "value": "1000", "metadata": {"change": "-15"}}]}
    answer, confidence = render_grounded_response("How is my business doing?", "business_health", context)
    assert confidence == "grounded"
    assert "1,000" in answer
    # change is already a percentage value; must render as -15.0%, not -1500.0%.
    assert "-15.0%" in answer


def test_business_health_without_evidence_is_not_grounded():
    answer, confidence = render_grounded_response("How is my business doing?", "business_health", {})
    assert confidence == "insufficient_evidence"
    assert "don't have enough" in answer


def test_sales_performance_without_evidence_is_not_grounded():
    answer, confidence = render_grounded_response("What are my sales?", "sales_performance", {})
    assert confidence == "insufficient_evidence"


def test_general_intent_is_not_grounded():
    answer, confidence = render_grounded_response("What should I name my dog?", "general_business", {})
    assert confidence == "insufficient_evidence"
