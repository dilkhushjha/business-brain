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


def test_margin_analysis_with_evidence_is_grounded():
    context = {
        "evidence": [{"metric": "gross_margin_pct", "value": "12.5",
                      "metadata": {"revenue": 100000, "cost": 87500, "gross_profit": 12500, "cost_coverage_pct": 100}}],
        "signals": [],
    }
    answer, confidence = render_grounded_response("Why is my margin so low?", "margin_analysis", context)
    assert confidence == "grounded"
    assert "12.5%" in answer


def test_margin_analysis_cites_worst_product_signal():
    context = {
        "evidence": [{"metric": "gross_margin_pct", "value": "12.5", "metadata": {"revenue": 100000, "cost": 87500}}],
        "signals": [{"code": "PRODUCT_MARGIN_DETERIORATION", "evidence": {"product": "Clearance Item"}}],
    }
    answer, confidence = render_grounded_response("Why is my margin low?", "margin_analysis", context)
    assert confidence == "grounded"
    assert "Clearance Item" in answer


def test_margin_analysis_without_evidence_is_not_grounded():
    answer, confidence = render_grounded_response("Why is my margin low?", "margin_analysis", {})
    assert confidence == "insufficient_evidence"


def test_receivables_analysis_with_evidence_is_grounded():
    context = {
        "evidence": [{"metric": "receivables_outstanding", "value": "50000", "metadata": {"overdue": 20000}}],
        "signals": [{"code": "RECEIVABLE_OVERDUE", "evidence": {"customer": "ABC Electrical"}}],
    }
    answer, confidence = render_grounded_response("Who owes me money?", "receivables_analysis", context)
    assert confidence == "grounded"
    assert "ABC Electrical" in answer


def test_receivables_analysis_without_evidence_is_not_grounded():
    answer, confidence = render_grounded_response("Who owes me money?", "receivables_analysis", {})
    assert confidence == "insufficient_evidence"


def test_payables_analysis_with_evidence_is_grounded():
    context = {
        "evidence": [{"metric": "payables_outstanding", "value": "30000", "metadata": {"overdue": 10000}}],
        "signals": [{"code": "PAYABLE_OVERDUE", "evidence": {"supplier": "ABC Distributors"}}],
    }
    answer, confidence = render_grounded_response("What do I owe?", "payables_analysis", context)
    assert confidence == "grounded"
    assert "ABC Distributors" in answer


def test_supplier_analysis_with_price_signal_is_grounded():
    context = {
        "evidence": [],
        "signals": [{"code": "SUPPLIER_PRICE_INCREASE", "evidence": {"supplier": "ABC Distributors", "product": "LED Bulb 9W"}}],
    }
    answer, confidence = render_grounded_response("Have my suppliers raised prices?", "supplier_analysis", context)
    assert confidence == "grounded"
    assert "ABC Distributors" in answer
    assert "LED Bulb 9W" in answer


def test_supplier_analysis_without_evidence_is_not_grounded():
    answer, confidence = render_grounded_response("Have my suppliers raised prices?", "supplier_analysis", {})
    assert confidence == "insufficient_evidence"


def test_customer_analysis_cites_declining_customers():
    context = {
        "evidence": [],
        "signals": [{"code": "CUSTOMER_REVENUE_DECLINE", "evidence": {"customer": "Acme Traders"}}],
    }
    answer, confidence = render_grounded_response("Which customers are at risk?", "customer_analysis", context)
    assert confidence == "grounded"
    assert "Acme Traders" in answer


def test_customer_analysis_falls_back_to_concentration_when_no_decline_signals():
    context = {
        "evidence": [{"metric": "customer_concentration_top_share_pct", "value": "42.0",
                      "metadata": {"top_customers": [{"name": "Big Co", "share_pct": 42.0}]}}],
        "signals": [],
    }
    answer, confidence = render_grounded_response("Which customers are at risk?", "customer_analysis", context)
    assert confidence == "grounded"
    assert "Big Co" in answer


def test_customer_analysis_without_evidence_is_not_grounded():
    answer, confidence = render_grounded_response("Which customers are at risk?", "customer_analysis", {})
    assert confidence == "insufficient_evidence"


def test_product_analysis_cites_signals():
    context = {
        "evidence": [],
        "signals": [{"code": "PRODUCT_SLOW_MOVING", "evidence": {"product": "Winter Jacket"}}],
    }
    answer, confidence = render_grounded_response("Which products aren't selling?", "product_analysis", context)
    assert confidence == "grounded"
    assert "Winter Jacket" in answer


def test_product_analysis_without_evidence_is_not_grounded():
    answer, confidence = render_grounded_response("Which products aren't selling?", "product_analysis", {})
    assert confidence == "insufficient_evidence"


def test_root_cause_cites_top_signal_as_a_hypothesis_not_a_certainty():
    context = {
        "evidence": [],
        "signals": [{"code": "CUSTOMER_REVENUE_DECLINE", "title": "Acme Traders is buying less", "evidence": {}}],
    }
    answer, confidence = render_grounded_response("Why did my sales fall?", "root_cause", context)
    assert confidence == "grounded"
    assert "Acme Traders is buying less" in answer
    assert "can't assign a single definitive cause" in answer


def test_root_cause_without_signals_is_not_grounded():
    answer, confidence = render_grounded_response("Why did this happen?", "root_cause", {})
    assert confidence == "insufficient_evidence"
