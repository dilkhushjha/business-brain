from packages.agent.business_brain.agent.intent import classify_intent


def test_business_health_intent():
    assert classify_intent("How is my business doing overall?") == "business_health"


def test_sales_performance_intent():
    assert classify_intent("What's my revenue this month?") == "sales_performance"


def test_margin_analysis_intent():
    assert classify_intent("Why is my margin so low?") == "margin_analysis"
    assert classify_intent("What's my profitability like?") == "margin_analysis"


def test_receivables_analysis_intent():
    assert classify_intent("Who owes me money?") == "receivables_analysis"
    assert classify_intent("What are my outstanding receivables?") == "receivables_analysis"


def test_payables_analysis_intent():
    assert classify_intent("What bills do I have due?") == "payables_analysis"
    assert classify_intent("What do I owe my suppliers?") == "payables_analysis"


def test_supplier_analysis_intent():
    assert classify_intent("Have any of my suppliers raised prices?") == "supplier_analysis"


def test_expense_analysis_intent():
    assert classify_intent("What are my expenses this month?") == "expense_analysis"
    assert classify_intent("Why are my overhead costs so high?") == "expense_analysis"


def test_purchase_cost_still_hits_supplier_not_expense():
    """Regression guard: 'purchase cost' (supplier_analysis) must not get
    swallowed by expense_analysis's broader cost-related keywords."""
    assert classify_intent("Why did my purchase cost go up?") == "supplier_analysis"


def test_customer_analysis_intent():
    assert classify_intent("Which customers are at risk?") == "customer_analysis"


def test_product_analysis_intent():
    assert classify_intent("Which products aren't selling well?") == "product_analysis"


def test_root_cause_intent():
    assert classify_intent("Why did this happen?") == "root_cause"


def test_general_business_fallback():
    assert classify_intent("What's the weather like today?") == "general_business"


def test_margin_takes_priority_over_root_cause_for_why_questions():
    """'why is my margin low' should be recognized specifically as a margin
    question, not fall through to the generic root_cause bucket -- more
    specific categories are checked first."""
    assert classify_intent("Why is my margin so thin this month?") == "margin_analysis"
