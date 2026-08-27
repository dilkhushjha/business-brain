from decimal import Decimal

from packages.analytics.business_brain.metrics.core import gross_margin, revenue_growth


def test_gross_margin():
    result = gross_margin(Decimal("1000"), Decimal("700"))
    assert result.value == Decimal("0.3")
    assert result.name == "gross_margin"


def test_revenue_growth():
    result = revenue_growth(Decimal("120"), Decimal("100"))
    assert result.value == Decimal("0.2")
