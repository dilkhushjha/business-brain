from decimal import Decimal

from packages.analytics.business_brain.drivers.calculator import rank_drivers


def test_rank_drivers_by_absolute_contribution():
    result = rank_drivers(
        "revenue",
        Decimal("850"),
        Decimal("1000"),
        {"A": Decimal("500"), "B": Decimal("350")},
        {"A": Decimal("600"), "B": Decimal("400")},
        "customer",
    )
    assert result.delta == Decimal("-150")
    assert result.drivers[0].key == "A"
    assert result.drivers[0].contribution == Decimal("-100")
    assert result.drivers[1].contribution == Decimal("-50")
