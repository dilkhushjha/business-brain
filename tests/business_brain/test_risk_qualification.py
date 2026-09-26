from decimal import Decimal

from packages.analytics.business_brain.risk import detect_business_risks
from packages.analytics.business_brain.signals.models import Signal


def _signal(code, severity="warning", confidence="0.85"):
    return Signal(
        code=code,
        title=code,
        severity=severity,
        confidence=Decimal(confidence),
        metric="test",
        current_value=Decimal("1"),
        baseline_value=None,
        change=None,
        evidence={},
        recommended_next_step="Review",
    )


def test_supplier_concentration_is_part_of_supplier_risk():
    risks = detect_business_risks([_signal("SUPPLIER_CONCENTRATION")])
    risk = next(item for item in risks if item.code == "SUPPLIER_RISK")
    assert "SUPPLIER_CONCENTRATION" in risk.signal_codes


def test_inventory_integrity_qualifies_inventory_risk():
    risks = detect_business_risks(
        [_signal("STOCKOUT_RISK", severity="critical", confidence="0.95")],
        {
            "status": "attention_required",
            "affected_domains": ["inventory"],
        },
    )
    risk = next(item for item in risks if item.code == "INVENTORY_RISK")
    assert risk.confidence == Decimal("0.65")
    assert risk.score <= Decimal("69")


def test_unrelated_integrity_domain_does_not_qualify_cash_risk():
    risks = detect_business_risks(
        [_signal("RECEIVABLE_OVERDUE")],
        {
            "status": "attention_required",
            "affected_domains": ["inventory"],
        },
    )
    risk = next(item for item in risks if item.code == "CASH_FLOW_RISK")
    assert risk.confidence == Decimal("0.85")
