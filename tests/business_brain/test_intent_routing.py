from packages.agent.business_brain.agent.intent import classify_intent


def test_natural_why_questions_route_to_root_cause():
    assert classify_intent("Why is my margin low?") == "root_cause"
    assert classify_intent("Why did sales drop?") == "root_cause"
    assert classify_intent("Why are expenses increasing?") == "root_cause"


def test_direct_metric_questions_keep_metric_intent():
    assert classify_intent("What is my gross margin?") == "margin_analysis"
    assert classify_intent("How much do customers owe me?") == "receivables_analysis"
    assert classify_intent("What do I owe suppliers?") == "payables_analysis"


def test_action_questions_route_to_decision_support():
    assert classify_intent("What should I do about supplier costs?") == "decision_support"
    assert classify_intent("What needs my attention?") == "decision_support"
