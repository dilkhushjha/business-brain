from packages.agent.business_brain.agent.intent import classify_intent


def test_intent_classification_prioritizes_decision_questions():
    assert classify_intent("What should I do about falling sales?") == "decision_support"
    assert classify_intent("What needs my attention right now?") == "decision_support"


def test_intent_classification_covers_business_history_and_integrity():
    assert classify_intent("What changed in my business?") == "situation_history"
    assert classify_intent("Can I trust the data?") == "data_integrity"


def test_intent_classification_keeps_specific_financial_questions():
    assert classify_intent("Why is my margin falling?") == "margin_analysis"
    assert classify_intent("How much do customers owe me?") == "receivables_analysis"
    assert classify_intent("How much do I owe suppliers?") == "payables_analysis"
