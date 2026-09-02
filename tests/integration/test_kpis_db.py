from datetime import date
from decimal import Decimal

from packages.analytics.business_brain.query.sales import sales_summary
from packages.analytics.business_brain.service import monthly_sales_kpis


def _kpi(kpis, name):
    return next(k for k in kpis if k.name == name)


def test_monthly_sales_kpis_compares_current_vs_previous_month(db_session, seeder):
    from packages.analytics.business_brain.metrics.time_windows import current_month, previous_month

    business = seeder.business()
    product = seeder.product(business.id, "LED Bulb 9W")
    as_of = date.today()
    current_window = current_month(as_of)
    prev_window = previous_month(as_of)

    # Anchor to the window boundaries themselves (always inside the window,
    # regardless of where "today" happens to fall in the calendar month --
    # e.g. days_ago=2 would wrongly spill into the previous month if today
    # is the 1st or 2nd of the month).
    seeder.sale_with_line(business.id, product.id, days_ago=(as_of - current_window.start).days,
                           quantity=10, unit_price=100)
    seeder.sale_with_line(business.id, product.id, days_ago=(as_of - current_window.end).days,
                           quantity=5, unit_price=100)
    seeder.sale_with_line(business.id, product.id, days_ago=(as_of - prev_window.end).days,
                           quantity=10, unit_price=100)

    kpis = monthly_sales_kpis(db_session, business.id, as_of)
    revenue = _kpi(kpis, "revenue")

    assert revenue.value == Decimal("1500")
    assert revenue.comparison_value == Decimal("1000")
    assert revenue.change == Decimal("50")  # (1500-1000)/1000 * 100


def test_monthly_sales_kpis_ignores_other_businesses(db_session, seeder):
    business = seeder.business("Business A")
    other = seeder.business("Business B")
    product_a = seeder.product(business.id, "Widget")
    product_b = seeder.product(other.id, "Gadget")

    seeder.sale_with_line(business.id, product_a.id, days_ago=1, quantity=1, unit_price=500)
    seeder.sale_with_line(other.id, product_b.id, days_ago=1, quantity=1, unit_price=9999)

    kpis = monthly_sales_kpis(db_session, business.id, date.today())
    assert _kpi(kpis, "revenue").value == Decimal("500")


def test_monthly_sales_kpis_with_no_data_returns_none_change(db_session, seeder):
    business = seeder.business()
    kpis = monthly_sales_kpis(db_session, business.id, date.today())
    revenue = _kpi(kpis, "revenue")
    assert revenue.value == Decimal("0")
    assert revenue.change is None  # growth() returns None when previous == 0


def test_invoice_count_and_revenue_are_not_inflated_by_multi_line_invoices(db_session, seeder):
    """Regression test for a real bug: sales_summary() used to join
    sale_lines and aggregate over that joined result, which duplicates each
    sale row once per line -- so a single 2-line invoice inflated BOTH
    invoice_count (counted as 2 invoices) AND revenue (total_amount summed
    twice). Fixed by computing revenue/invoice_count directly from
    SaleModel and units_sold via a separate join."""
    business = seeder.business()
    product_a = seeder.product(business.id, "Product A")
    product_b = seeder.product(business.id, "Product B")

    # total_amount is deliberately different from the sum of the lines
    # (100 + 200 = 300) to make any row-fan-out doubling obvious.
    sale = seeder.sale(business.id, days_ago=1, total_amount=Decimal("999"))
    seeder.sale_line(sale.id, product_a.id, quantity=1, unit_price=100)
    seeder.sale_line(sale.id, product_b.id, quantity=2, unit_price=100)

    kpis = monthly_sales_kpis(db_session, business.id, date.today())
    revenue = _kpi(kpis, "revenue")
    invoice_count = _kpi(kpis, "invoice_count")
    units = _kpi(kpis, "units_sold")

    assert revenue.value == Decimal("999")
    assert invoice_count.value == 1
    assert units.value == Decimal("3")  # 1 + 2 units across the two lines


def test_sale_with_no_line_items_still_counts_toward_revenue(db_session, seeder):
    """A sale with zero sale_lines used to be silently excluded from
    revenue/invoice_count entirely, because the old query INNER JOINed
    sale_lines. It's a real sale and should still count."""
    business = seeder.business()
    seeder.sale(business.id, days_ago=1, total_amount=Decimal("500"))

    kpis = monthly_sales_kpis(db_session, business.id, date.today())
    assert _kpi(kpis, "revenue").value == Decimal("500")
    assert _kpi(kpis, "invoice_count").value == 1
    assert _kpi(kpis, "units_sold").value == Decimal("0")


def test_sales_summary_directly_with_multiple_multi_line_invoices(db_session, seeder):
    """Direct test of sales_summary() (not routed through monthly_sales_kpis)
    with several multi-line invoices, to pin down the fix at the source."""
    business = seeder.business()
    product = seeder.product(business.id, "Widget")

    sale1 = seeder.sale(business.id, days_ago=0, total_amount=Decimal("300"))
    seeder.sale_line(sale1.id, product.id, quantity=1, unit_price=100)
    seeder.sale_line(sale1.id, product.id, quantity=2, unit_price=100)

    sale2 = seeder.sale(business.id, days_ago=0, total_amount=Decimal("700"))
    seeder.sale_line(sale2.id, product.id, quantity=1, unit_price=200)
    seeder.sale_line(sale2.id, product.id, quantity=1, unit_price=500)
    seeder.sale_line(sale2.id, product.id, quantity=3, unit_price=0)  # free-goods line

    result = sales_summary(db_session, business.id, date.today(), date.today())
    assert result.revenue == Decimal("1000")  # 300 + 700, not double-counted
    assert result.invoice_count == 2
    assert result.units == Decimal("8")  # (1+2) + (1+1+3)
