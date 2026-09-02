from decimal import Decimal

from packages.analytics.business_brain.drivers.calculator import rank_drivers
from packages.analytics.business_brain.recommendations.models import RecommendationContext
from packages.analytics.business_brain.recommendations.rules import generate_recommendations
from packages.analytics.business_brain.signals.models import Signal
from packages.analytics.business_brain.signals.rules import detect_kpi_signals
from packages.analytics.business_brain.metrics.kpis import KPI
from packages.ingestion.business_brain.ingestion.field_mapping import suggest_mapping
from packages.ingestion.business_brain.ingestion.normalizer import normalize_record
from packages.ingestion.business_brain.ingestion.schema_profiler import profile_rows
from packages.ingestion.business_brain.ingestion.validation import validate_records


def test_v1_happy_path_from_messy_record_to_recommendation():
    rows = [
        {"Bill Date": "27-08-2026", "Party Name": "ABC Electrical", "Qty": "1,200", "Rate": "80", "Net Amount": "₹ 96,000"},
        {"Bill Date": "28/08/2026", "Party Name": "XYZ Traders", "Qty": "100", "Rate": "220", "Net Amount": "₹ 22,000"},
    ]
    profile = profile_rows(rows)
    assert profile.row_count == 2

    matches = suggest_mapping([column.name for column in profile.columns])
    mapping = {match.source: match.target for match in matches}
    # The fixture deliberately uses real-world aliases; all core fields must map.
    assert {"date", "customer", "quantity", "unit_price", "amount"}.issubset(mapping.values())

    issues = validate_records(rows, mapping)
    assert issues == []

    normalized = [normalize_record(row, mapping) for row in rows]
    assert normalized[0]["amount"] == Decimal("96000")
    assert normalized[0]["quantity"] == Decimal("1200")

    kpis = [KPI("revenue", Decimal("850000"), "INR", "current_month", Decimal("1000000"), Decimal("-15"))]
    signals = detect_kpi_signals(kpis)
    assert len(signals) == 1
    assert signals[0].code == "REVENUE_DECLINE"

    recommendations = generate_recommendations(RecommendationContext(signals=signals, drivers=[]))
    assert recommendations[0].code == "INVESTIGATE_REVENUE_DECLINE"
    assert recommendations[0].evidence["signal"] == "REVENUE_DECLINE"


def test_v1_driver_analysis_identifies_largest_contributor():
    result = rank_drivers(
        "revenue",
        Decimal("850000"),
        Decimal("1000000"),
        {"ABC Electrical": Decimal("500000"), "XYZ Traders": Decimal("350000")},
        {"ABC Electrical": Decimal("600000"), "XYZ Traders": Decimal("400000")},
        "customer",
    )
    assert result.delta == Decimal("-150000")
    assert result.drivers[0].key == "ABC Electrical"
    assert result.drivers[0].contribution == Decimal("-100000")


def test_v1_does_not_create_decline_signal_for_growth():
    kpis = [KPI("revenue", Decimal("1100000"), "INR", "current_month", Decimal("1000000"), Decimal("10"))]
    assert detect_kpi_signals(kpis) == []


def test_v1_no_customer_evidence_means_no_claim():
    # The response layer receives no customer evidence. The test protects the
    # product contract: unsupported customer causality must never be fabricated.
    signal = Signal(
        code="REVENUE_DECLINE",
        title="Revenue is declining",
        severity="warning",
        confidence=Decimal("0.90"),
        metric="revenue",
        current_value=Decimal("850000"),
        baseline_value=Decimal("1000000"),
        change=Decimal("-15"),
        evidence={"rule": "change <= -10%"},
        recommended_next_step="Investigate the drivers of the revenue decline.",
    )
    recommendations = generate_recommendations(RecommendationContext(signals=[signal], drivers=[]))
    text = " ".join(recommendations[0].actions).lower()
    assert "customer" in text
    assert "abc electrical" not in text
