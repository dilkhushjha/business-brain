from decimal import Decimal

from packages.analytics.business_brain.metrics.inventory import dead_stock, demand_spikes


def test_demand_spike_flags_material_velocity_increase(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Umbrella")
    # Previous 30-day window: 10 units.
    seeder.sale_with_line(business.id, product.id, days_ago=45, quantity=10, unit_price=100)
    # Current 30-day window: 30 units -- a 200% increase.
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=30, unit_price=100)

    result = demand_spikes(db_session, business.id)
    assert len(result) == 1
    assert result[0]["name"] == "Umbrella"
    assert result[0]["change_pct"] == 200.0
    assert result[0]["severity"] == "high"


def test_demand_spike_ignores_stable_velocity(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Steady Widget")
    seeder.sale_with_line(business.id, product.id, days_ago=45, quantity=10, unit_price=100)
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=11, unit_price=100)  # only 10% rise

    assert demand_spikes(db_session, business.id) == []


def test_demand_spike_ignores_product_with_no_prior_sales(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "New Product")
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=50, unit_price=100)

    assert demand_spikes(db_session, business.id) == []


def test_dead_stock_flags_zero_velocity_with_real_stock(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Forgotten Item")
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=200, value=2000)
    # No sales at all for this product.

    result = dead_stock(db_session, business.id)
    assert len(result) == 1
    assert result[0]["name"] == "Forgotten Item"
    assert result[0]["quantity_on_hand"] == 200.0


def test_dead_stock_ignores_product_with_recent_sales(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Active Item")
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=1, unit_price=100)
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=200, value=2000)

    assert dead_stock(db_session, business.id) == []


def test_dead_stock_ignores_zero_stock(db_session, seeder):
    """A product with no stock on hand at all isn't 'dead stock' -- there's
    nothing tying up capital."""
    business = seeder.business()
    product = seeder.product(business.id, "Out Of Stock Item")
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=0, value=0)

    assert dead_stock(db_session, business.id) == []


def test_dead_stock_ignores_stale_snapshot(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Stale Snapshot Item")
    seeder.inventory_snapshot(business.id, product.id, days_ago=60, quantity=200, value=2000)

    assert dead_stock(db_session, business.id) == []
