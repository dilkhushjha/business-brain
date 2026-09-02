from packages.analytics.business_brain.metrics.margin import (
    low_margin_products,
    margin_summary,
)


def test_margin_summary_computes_gross_margin(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "LED Bulb 9W")
    seeder.sale_with_line(business.id, product.id, days_ago=5,
                           quantity=10, unit_price=100, cost_price=60)

    result = margin_summary(db_session, business.id)
    assert result["revenue"] == 1000.0
    assert result["cost"] == 600.0
    assert result["gross_profit"] == 400.0
    assert result["gross_margin_pct"] == 40.0


def test_margin_summary_excludes_lines_without_cost_price(db_session, seeder):
    """Lines with no recorded cost aren't included in cost/covered revenue,
    which is why cost_coverage_pct exists -- confirm it reflects that."""
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    seeder.sale_with_line(business.id, product.id, days_ago=5,
                           quantity=10, unit_price=100, cost_price=60)
    seeder.sale_with_line(business.id, product.id, days_ago=5,
                           quantity=5, unit_price=100, cost_price=None)

    result = margin_summary(db_session, business.id)
    assert result["revenue"] == 1500.0  # both lines count toward revenue
    assert result["cost"] == 600.0  # only the costed line
    assert result["cost_coverage_pct"] < 100.0


def test_low_margin_products_flags_negative_margin_as_high_severity(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Clearance Item")
    # Selling below cost: 10 units at 50 revenue vs 60 cost each.
    seeder.sale_with_line(business.id, product.id, days_ago=5,
                           quantity=10, unit_price=50, cost_price=60)

    result = low_margin_products(db_session, business.id, threshold=10)
    assert len(result) == 1
    assert result[0]["name"] == "Clearance Item"
    assert result[0]["severity"] == "high"
    assert result[0]["margin_pct"] < 0


def test_low_margin_products_excludes_healthy_margin(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Healthy Item")
    seeder.sale_with_line(business.id, product.id, days_ago=5,
                           quantity=10, unit_price=100, cost_price=50)  # 50% margin

    assert low_margin_products(db_session, business.id, threshold=10) == []
