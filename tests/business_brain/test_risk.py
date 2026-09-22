from decimal import Decimal
from types import SimpleNamespace

from packages.analytics.business_brain.risk import detect_business_risks


def _signal(code, severity="warning", confidence="0.80", evidence=None):
    return SimpleNamespace(
        code=code,
        title=code.replace("_", " ").title(),
        severity=severity,
        confidence=Decimal(confidence),
        evidence=evidence or {},
    )


def test_risk_engine_aggregates_multiple_cash_flow_signals():
    risks = detect_business_risks([
        _signal("RECEIVABLE_OVERDUE", "critical", "0.95", {"customer": "Alpha"}),
        _signal("PAYABLE_OVERDUE", "warning", "0.85", {"supplier": "Prime"}),
    ])

    assert len(risks) == 1
    risk = risks[0]
    assert risk.code == "CASH_FLOW_RISK"
    assert risk.level in {"high", "critical"}
    assert risk.score > Decimal("55")
    assert set(risk.signal_codes) == {"RECEIVABLE_OVERDUE", "PAYABLE_OVERDUE"}
    assert risk.evidence["signals"]


def test_risk_engine_does_not_create_risk_without_evidence():
    assert detect_business_risks([]) == []


def test_risk_engine_surfaces_data_integrity_as_risk_context():
    risks = detect_business_risks(
        [_signal("NEGATIVE_INVENTORY", "critical", "0.98", {"product": "Cable"})],
        {
            "status": "attention_required",
            "affected_domains": ["inventory"],
        },
    )

    codes = {risk.code for risk in risks}
    assert "INVENTORY_RISK" in codes
    assert "DATA_INTEGRITY_RISK" in codes

    inventory = next(risk for risk in risks if risk.code == "INVENTORY_RISK")
    assert inventory.evidence["integrity_status"] == "attention_required"


def test_risk_engine_is_deterministically_ordered():
    risks = detect_business_risks([
        _signal("CUSTOMER_INACTIVE", "warning", "0.80"),
        _signal("PRODUCT_MARGIN_DETERIORATION", "warning", "0.85"),
        _signal("SUPPLIER_PRICE_INCREASE", "warning", "0.85"),
    ])

    assert [risk.code for risk in risks] == sorted(
        [risk.code for risk in risks],
        key=lambda code: next(
            risk.score for risk in risks if risk.code == code
        ),
        reverse=True,
    )
