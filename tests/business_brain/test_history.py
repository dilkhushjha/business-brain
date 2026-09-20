from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from packages.analytics.business_brain.history import record_situation_history, load_situation_history


def situation(code="MARGIN_PRESSURE", score="60", confidence="0.8"):
    return SimpleNamespace(
        code=code,
        title="Margin pressure",
        severity="warning",
        confidence=Decimal(confidence),
        explanation="Supplier costs overlap with thin margins.",
        evidence={"products": ["Cable"]},
    )


def priority(code="MARGIN_PRESSURE", score="60"):
    return SimpleNamespace(situation_code=code, score=Decimal(score), level="attention")


def test_new_situation_is_recorded_as_active(db_session, seeder):
    business = seeder.business()
    result = record_situation_history(
        db_session, business.id, date(2026, 9, 1), [situation()], [priority()]
    )

    assert result[0].status == "active"
    assert result[0].trend == "new"
    assert result[0].first_seen_at == date(2026, 9, 1)
    assert result[0].last_seen_at == date(2026, 9, 1)


def test_repeated_situation_tracks_worsening_and_improving(db_session, seeder):
    business = seeder.business()

    record_situation_history(
        db_session, business.id, date(2026, 9, 1), [situation(score="50")], [priority(score="50")]
    )
    second = record_situation_history(
        db_session, business.id, date(2026, 9, 5), [situation(score="65")], [priority(score="65")]
    )
    assert second[0].trend == "worsening"
    assert second[0].first_seen_at == date(2026, 9, 1)

    third = record_situation_history(
        db_session, business.id, date(2026, 9, 8), [situation(score="55")], [priority(score="55")]
    )
    assert third[0].trend == "improving"


def test_missing_situation_is_marked_resolved(db_session, seeder):
    business = seeder.business()

    record_situation_history(
        db_session, business.id, date(2026, 9, 1), [situation()], [priority()]
    )
    result = record_situation_history(
        db_session, business.id, date(2026, 9, 10), [], []
    )

    assert len(result) == 1
    assert result[0].status == "resolved"
    assert result[0].trend == "resolved"
    assert result[0].resolved_at == date(2026, 9, 10)

    loaded = load_situation_history(db_session, business.id)
    assert loaded[0].status == "resolved"
