from decimal import Decimal

from packages.analytics.business_brain.qualification import qualify_situations
from packages.analytics.business_brain.correlations import BusinessSituation


def _situation(code: str, confidence: str = "0.90") -> BusinessSituation:
    return BusinessSituation(
        code=code,
        title="Test situation",
        severity="warning",
        confidence=Decimal(confidence),
        signal_codes=["TEST"],
        evidence={"source": "test"},
        explanation="Original explanation.",
        recommended_next_step="Review evidence.",
    )


def test_unaffected_situation_keeps_confidence():
    situation = _situation("MARGIN_PRESSURE")
    result = qualify_situations([situation], {"affected_domains": ["financial"]})

    assert result[0].confidence == Decimal("0.90")
    assert "integrity_status" not in result[0].evidence


def test_relevant_integrity_issue_qualifies_situation():
    situation = _situation("WORKING_CAPITAL_PRESSURE", "0.86")
    result = qualify_situations(
        [situation],
        {
            "status": "attention_required",
            "affected_domains": ["financial"],
        },
    )

    assert result[0].confidence == Decimal("0.65")
    assert result[0].evidence["integrity_status"] == "attention_required"
    assert result[0].evidence["integrity_domains"] == ["financial"]
    assert "qualified" in result[0].explanation


def test_data_quality_issue_qualifies_cross_domain_situation():
    situation = _situation("MARGIN_PRESSURE")
    result = qualify_situations(
        [situation],
        {
            "status": "attention_required",
            "affected_domains": ["data_quality"],
        },
    )

    assert result[0].confidence == Decimal("0.65")
    assert result[0].evidence["integrity_domains"] == ["data_quality"]


def test_clean_integrity_does_not_change_situations():
    situation = _situation("MARGIN_PRESSURE")
    result = qualify_situations(
        [situation],
        {
            "status": "reconciled",
            "affected_domains": [],
        },
    )

    assert result[0] == situation


def test_many_integrity_issues_lower_confidence_further():
    situation = _situation("MARGIN_PRESSURE")
    result = qualify_situations([situation], {"status": "attention_required", "affected_domains": ["data_quality"], "audits": {"data_quality": {"summary": {"issue_count": 5}}}})
    assert result[0].confidence == Decimal("0.40")
