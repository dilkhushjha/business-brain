from decimal import Decimal

from packages.analytics.business_brain.metrics.supplier_risk import (
    supplier_concentration,
    supplier_price_increases,
)


def test_supplier_concentration_computes_share_of_spend(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    big = seeder.supplier(business.id, "Big Supplier")
    small = seeder.supplier(business.id, "Small Supplier")

    seeder.purchase_with_line(business.id, product.id, supplier_id=big.id,
                               days_ago=5, quantity=1, unit_cost=8000)
    seeder.purchase_with_line(business.id, product.id, supplier_id=small.id,
                               days_ago=5, quantity=1, unit_cost=2000)

    result = supplier_concentration(db_session, business.id, top_n=5)
    assert result["total_spend"] == 10000.0
    assert result["top_suppliers"][0]["name"] == "Big Supplier"
    assert result["top_suppliers"][0]["share_pct"] == 80.0
    assert result["risk"] == "high"  # single supplier >= 35% share


def test_supplier_price_increase_flags_material_cost_rise(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "LED Bulb 9W")
    supplier = seeder.supplier(business.id, "ABC Distributors")

    # Previous 30-day window: cheaper.
    seeder.purchase_with_line(business.id, product.id, supplier_id=supplier.id,
                               days_ago=45, quantity=100, unit_cost=50)
    # Current 30-day window: cost jumped materially.
    seeder.purchase_with_line(business.id, product.id, supplier_id=supplier.id,
                               days_ago=5, quantity=100, unit_cost=70)

    result = supplier_price_increases(db_session, business.id)
    assert len(result) == 1
    assert result[0]["supplier"] == "ABC Distributors"
    assert result[0]["product"] == "LED Bulb 9W"
    assert result[0]["change_pct"] == 40.0  # (70-50)/50 * 100
    assert result[0]["severity"] == "high"


def test_supplier_price_increase_ignores_stable_cost(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    supplier = seeder.supplier(business.id, "Steady Supplier")

    seeder.purchase_with_line(business.id, product.id, supplier_id=supplier.id,
                               days_ago=45, quantity=10, unit_cost=100)
    seeder.purchase_with_line(business.id, product.id, supplier_id=supplier.id,
                               days_ago=5, quantity=10, unit_cost=102)  # only 2% rise

    assert supplier_price_increases(db_session, business.id) == []


def test_supplier_price_increase_ignores_product_with_no_prior_purchases(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "New Product")
    supplier = seeder.supplier(business.id, "New Supplier")
    seeder.purchase_with_line(business.id, product.id, supplier_id=supplier.id,
                               days_ago=5, quantity=1, unit_cost=100)

    assert supplier_price_increases(db_session, business.id) == []
