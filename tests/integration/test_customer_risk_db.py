from decimal import Decimal

from packages.analytics.business_brain.metrics.customer_risk import (
    customer_concentration,
    declining_customers,
    inactive_customers,
)


def test_declining_customers_flags_material_drop(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Acme Traders")

    # Previous 30-day window (days 31-60 ago): strong revenue.
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=45, quantity=1, unit_price=20000)
    # Current 30-day window (last 30 days): revenue dropped materially.
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=5, quantity=1, unit_price=5000)

    result = declining_customers(db_session, business.id)
    assert len(result) == 1
    assert result[0]["name"] == "Acme Traders"
    assert result[0]["severity"] == "high"  # (20000-5000)/20000 = 75% >= 50%


def test_declining_customers_ignores_stable_customer(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Steady Co")

    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=45, quantity=1, unit_price=10000)
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=5, quantity=1, unit_price=9500)  # only 5% drop

    assert declining_customers(db_session, business.id) == []


def test_inactive_customers_flags_no_recent_orders(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Gone Quiet Ltd")

    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=90, quantity=1, unit_price=1000)

    result = inactive_customers(db_session, business.id, inactive_days=45)
    assert len(result) == 1
    assert result[0]["name"] == "Gone Quiet Ltd"


def test_inactive_customers_excludes_recently_active(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Active Co")

    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=5, quantity=1, unit_price=1000)

    assert inactive_customers(db_session, business.id, inactive_days=45) == []


def test_customer_concentration_computes_share_of_revenue(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    big = seeder.customer(business.id, "Big Co")
    small = seeder.customer(business.id, "Small Co")

    seeder.sale_with_line(business.id, product.id, customer_id=big.id,
                           days_ago=5, quantity=1, unit_price=8000)
    seeder.sale_with_line(business.id, product.id, customer_id=small.id,
                           days_ago=5, quantity=1, unit_price=2000)

    result = customer_concentration(db_session, business.id, top_n=5)
    assert result["total_revenue"] == 10000.0
    assert result["top_customers"][0]["name"] == "Big Co"
    assert result["top_customers"][0]["share_pct"] == 80.0
    assert result["risk"] == "high"  # single customer >= 35% share
