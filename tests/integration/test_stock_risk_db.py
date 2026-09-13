from decimal import Decimal

from packages.analytics.business_brain.metrics.inventory import stock_risk


def test_stockout_risk_flags_low_days_of_cover(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "LED Bulb 9W")
    # Selling 10 units/day on average (300 over 30 days), only 20 on hand
    # -> 2 days of cover, well under the 7-day default threshold.
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=300, unit_price=10)
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=20, value=200)

    result = stock_risk(db_session, business.id)
    assert len(result["stockout_risk"]) == 1
    assert result["stockout_risk"][0]["name"] == "LED Bulb 9W"
    assert result["excess_inventory"] == []


def test_excess_inventory_flags_high_days_of_cover(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Slow Widget")
    # Selling 1 unit/day on average, but 500 on hand -> 500 days of cover.
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=30, unit_price=10)
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=500, value=5000)

    result = stock_risk(db_session, business.id)
    assert len(result["excess_inventory"]) == 1
    assert result["excess_inventory"][0]["name"] == "Slow Widget"
    assert result["stockout_risk"] == []


def test_stock_risk_ignores_healthy_days_of_cover(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Steady Product")
    # Selling 10 units/day, 200 on hand -> 20 days of cover, comfortably
    # within the default 7-90 day healthy range.
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=300, unit_price=10)
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=200, value=2000)

    result = stock_risk(db_session, business.id)
    assert result["stockout_risk"] == []
    assert result["excess_inventory"] == []


def test_stock_risk_ignores_product_with_no_recent_sales(db_session, seeder):
    """A product with stock but zero recent sales velocity isn't flagged
    as 'excess' by this function -- that's a different problem (dead
    stock), and dividing by zero velocity isn't meaningful."""
    business = seeder.business()
    product = seeder.product(business.id, "Never Sold Item")
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=1000, value=10000)

    result = stock_risk(db_session, business.id)
    assert result["stockout_risk"] == []
    assert result["excess_inventory"] == []


def test_stock_risk_ignores_stale_snapshot(db_session, seeder):
    """A snapshot older than snapshot_max_age_days shouldn't drive a
    stockout call -- the stock position might have changed a lot since."""
    business = seeder.business()
    product = seeder.product(business.id, "Stale Data Product")
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=300, unit_price=10)
    seeder.inventory_snapshot(business.id, product.id, days_ago=60, quantity=20, value=200)

    result = stock_risk(db_session, business.id)
    assert result["stockout_risk"] == []
    assert result["excess_inventory"] == []


def test_stock_risk_uses_the_most_recent_snapshot(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Multi Snapshot Item")
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=300, unit_price=10)
    seeder.inventory_snapshot(business.id, product.id, days_ago=20, quantity=500, value=5000)  # older, would be "excess"
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=20, value=200)  # newer, is "stockout"

    result = stock_risk(db_session, business.id)
    assert len(result["stockout_risk"]) == 1
    assert result["excess_inventory"] == []
