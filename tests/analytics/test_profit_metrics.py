from decimal import Decimal

from packages.analytics.business_brain.metrics.profit import gross_margin, gross_profit


def test_gross_profit():
    assert gross_profit(Decimal("1000"), Decimal("700")) == Decimal("300")


def test_gross_margin():
    assert gross_margin(Decimal("1000"), Decimal("700")) == Decimal("0.3")


def test_zero_revenue_margin_is_unknown():
    assert gross_margin(Decimal("0"), Decimal("700")) is None
