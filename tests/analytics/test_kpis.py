from datetime import date
from decimal import Decimal

from packages.analytics.business_brain.metrics.kpis import (
    average_invoice_value,
    customer_concentration,
    growth,
)
from packages.analytics.business_brain.metrics.time_windows import (
    current_month,
    previous_month,
    trailing_days,
)


def test_growth():
    assert growth(Decimal("120"), Decimal("100")) == Decimal("20")
    assert growth(Decimal("100"), Decimal("0")) is None


def test_average_invoice_value():
    assert average_invoice_value(Decimal("1000"), 4) == Decimal("250")
    assert average_invoice_value(Decimal("1000"), 0) is None


def test_customer_concentration():
    assert customer_concentration(Decimal("250"), Decimal("1000")) == Decimal("0.25")


def test_time_windows():
    as_of = date(2026, 8, 27)
    assert current_month(as_of).start == date(2026, 8, 1)
    assert previous_month(as_of).start == date(2026, 7, 1)
    assert previous_month(as_of).end == date(2026, 7, 31)
    assert trailing_days(as_of, 30).start == date(2026, 7, 29)


def test_kpi_compat_reexports_the_same_class_not_a_duplicate():
    """Regression test: kpi_compat.py used to independently redefine KPI/
    growth/average_invoice_value rather than re-exporting metrics.kpis's
    versions -- two structurally identical classes with the same name,
    silently duck-typed together everywhere nothing did an isinstance()
    check. Confirms the fix: both import paths now resolve to the exact
    same objects."""
    from packages.analytics.business_brain.metrics import kpi_compat, kpis

    assert kpi_compat.KPI is kpis.KPI
    assert kpi_compat.growth is kpis.growth
    assert kpi_compat.average_invoice_value is kpis.average_invoice_value
