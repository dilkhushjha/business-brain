from decimal import Decimal

from packages.analytics.business_brain.metrics.expenses import (
    expense_spikes,
    expense_summary,
)


def test_expense_summary_totals_by_category(db_session, seeder):
    business = seeder.business()
    seeder.expense(business.id, days_ago=5, category="Rent", amount=Decimal("25000"))
    seeder.expense(business.id, days_ago=5, category="Transport", amount=Decimal("5000"))
    seeder.expense(business.id, days_ago=5, category="Transport", amount=Decimal("2000"))

    result = expense_summary(db_session, business.id)
    assert result["total"] == 32000.0
    assert result["by_category"]["Rent"] == 25000.0
    assert result["by_category"]["Transport"] == 7000.0


def test_expense_spike_flags_material_category_increase(db_session, seeder):
    business = seeder.business()
    # Previous 30-day window: normal transport spend.
    seeder.expense(business.id, days_ago=45, category="Transport", amount=Decimal("5000"))
    # Current 30-day window: transport spend spiked.
    seeder.expense(business.id, days_ago=5, category="Transport", amount=Decimal("12000"))

    result = expense_spikes(db_session, business.id)
    assert len(result) == 1
    assert result[0]["category"] == "Transport"
    assert result[0]["change_pct"] == 140.0
    assert result[0]["severity"] == "high"


def test_expense_spike_ignores_stable_category(db_session, seeder):
    business = seeder.business()
    seeder.expense(business.id, days_ago=45, category="Rent", amount=Decimal("25000"))
    seeder.expense(business.id, days_ago=5, category="Rent", amount=Decimal("25500"))  # 2% rise

    assert expense_spikes(db_session, business.id) == []


def test_expense_spike_ignores_category_with_no_prior_spend(db_session, seeder):
    business = seeder.business()
    seeder.expense(business.id, days_ago=5, category="New Category", amount=Decimal("1000"))

    assert expense_spikes(db_session, business.id) == []
