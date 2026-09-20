from decimal import Decimal
from types import SimpleNamespace

from packages.analytics.business_brain.prioritization import prioritize_situations


def situation(code, severity="warning", confidence="0.85"):
    return SimpleNamespace(
        code=code,
        severity=severity,
        confidence=Decimal(confidence),
    )


def analysis(code, measurable=True):
    impact = SimpleNamespace(value=Decimal("100") if measurable else None)
    return SimpleNamespace(situation_code=code, impacts=[impact])


def test_critical_high_confidence_measurable_situation_is_immediate():
    result = prioritize_situations(
        [situation("WORKING_CAPITAL_PRESSURE", "critical", "0.90")],
        [analysis("WORKING_CAPITAL_PRESSURE")],
    )

    assert result[0].level == "immediate"
    assert result[0].score == Decimal("77.0")
    assert "has measurable impact evidence" in result[0].reasons


def test_missing_impact_does_not_get_invented():
    result = prioritize_situations(
        [situation("REVENUE_COST_SQUEEZE", "warning", "0.80")],
        [analysis("REVENUE_COST_SQUEEZE", measurable=False)],
    )

    assert result[0].score == Decimal("49.0")
    assert result[0].level == "attention"
    assert "no measurable impact value available" in result[0].reasons


def test_priorities_are_deterministic():
    situations = [
        situation("B", "warning", "0.80"),
        situation("A", "warning", "0.80"),
    ]

    result = prioritize_situations(situations)

    assert [item.situation_code for item in result] == ["A", "B"]
