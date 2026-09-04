from packages.analytics.business_brain.metrics.inventory import slow_moving_products


def test_slow_moving_products_flags_material_velocity_drop(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Winter Jacket")

    # Previous 30-day window: 20 units sold.
    seeder.sale_with_line(business.id, product.id, days_ago=45, quantity=20, unit_price=100)
    # Current 30-day window: only 2 units sold -- a 90% velocity drop.
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=2, unit_price=100)

    result = slow_moving_products(db_session, business.id)
    assert len(result) == 1
    assert result[0]["name"] == "Winter Jacket"
    assert result[0]["severity"] == "high"


def test_slow_moving_products_ignores_stable_product(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Steady Widget")

    seeder.sale_with_line(business.id, product.id, days_ago=45, quantity=10, unit_price=100)
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=9, unit_price=100)  # 10% drop only

    assert slow_moving_products(db_session, business.id) == []


def test_slow_moving_products_ignores_product_with_no_prior_period_sales(db_session, seeder):
    """A brand-new product with nothing to compare against shouldn't be
    flagged -- there's no prior-period baseline, not a genuine slowdown."""
    business = seeder.business()
    product = seeder.product(business.id, "New Launch")
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=1, unit_price=100)

    assert slow_moving_products(db_session, business.id) == []
