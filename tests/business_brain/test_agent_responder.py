from packages.agent.business_brain.agent.responder import render_grounded_response


def test_business_health_response_uses_cross_domain_context():
    answer, confidence = render_grounded_response(
        "How is my business doing?",
        "business_health",
        {
            "evidence": [
                {"metric": "revenue", "value": "12500", "metadata": {"change": "-8.5"}},
                {"metric": "gross_margin_pct", "value": "22.5"},
            ],
            "state": {"operating_surplus": "1800"},
            "signals": [],
            "situations": [
                {"code": "MARGIN_PRESSURE", "title": "Margin pressure"},
            ],
            "decision_actions": [
                {"title": "Investigate procurement-driven margin pressure"},
            ],
        },
    )

    assert confidence == "grounded"
    assert "₹12,500.00" in answer
    assert "-8.5%" in answer
    assert "22.5%" in answer
    assert "₹1,800.00" in answer
    assert "Margin pressure" in answer
    assert "Investigate procurement-driven margin pressure" in answer


def test_sales_response_mentions_relevant_entity_signal():
    answer, confidence = render_grounded_response(
        "How are sales doing?",
        "sales_performance",
        {
            "evidence": [
                {"metric": "revenue", "value": "9000", "metadata": {"change": "-12"}},
            ],
            "signals": [
                {
                    "code": "CUSTOMER_REVENUE_DECLINE",
                    "evidence": {"customer": "Alpha Traders"},
                }
            ],
            "situations": [],
            "recommendations": [],
        },
    )

    assert confidence == "grounded"
    assert "₹9,000.00" in answer
    assert "-12.0%" in answer
    assert "Alpha Traders" in answer
