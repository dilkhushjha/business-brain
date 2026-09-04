from datetime import date
from decimal import Decimal

from packages.analytics.business_brain.signals.engine import detect_signals


def test_detect_signals_surfaces_customer_decline_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Acme Traders")

    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=45, quantity=1, unit_price=20000)
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=5, quantity=1, unit_price=5000)

    signals = detect_signals(db_session, business.id, date.today())
    customer_signals = [s for s in signals if s.code == "CUSTOMER_REVENUE_DECLINE"]
    assert len(customer_signals) == 1
    assert customer_signals[0].evidence["customer"] == "Acme Traders"


def test_detect_signals_surfaces_margin_deterioration_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Clearance Item")
    seeder.sale_with_line(business.id, product.id, days_ago=5,
                           quantity=10, unit_price=50, cost_price=60)

    signals = detect_signals(db_session, business.id, date.today())
    margin_signals = [s for s in signals if s.code == "PRODUCT_MARGIN_DETERIORATION"]
    assert len(margin_signals) == 1
    assert margin_signals[0].evidence["product"] == "Clearance Item"
    assert margin_signals[0].severity == "critical"


def test_detect_signals_surfaces_overdue_receivable_from_real_data(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "ABC Electrical")
    seeder.sale(business.id, customer_id=customer.id, total_amount=Decimal("45000"),
                paid_amount=Decimal("0"), due_days_ago=75)

    signals = detect_signals(db_session, business.id, date.today())
    receivable_signals = [s for s in signals if s.code == "RECEIVABLE_OVERDUE"]
    assert len(receivable_signals) == 1
    assert receivable_signals[0].evidence["customer"] == "ABC Electrical"
    assert receivable_signals[0].evidence["days_overdue"] == 75


def test_detect_signals_surfaces_inactive_customer_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Gone Quiet Ltd")
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=90, quantity=1, unit_price=1000)

    signals = detect_signals(db_session, business.id, date.today())
    inactive_signals = [s for s in signals if s.code == "CUSTOMER_INACTIVE"]
    assert len(inactive_signals) == 1
    assert inactive_signals[0].evidence["customer"] == "Gone Quiet Ltd"


def test_detect_signals_surfaces_slow_moving_product_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Winter Jacket")
    seeder.sale_with_line(business.id, product.id, days_ago=45, quantity=20, unit_price=100)
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=2, unit_price=100)

    signals = detect_signals(db_session, business.id, date.today())
    slow_signals = [s for s in signals if s.code == "PRODUCT_SLOW_MOVING"]
    assert len(slow_signals) == 1
    assert slow_signals[0].evidence["product"] == "Winter Jacket"


def test_detect_signals_returns_empty_for_healthy_business(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Steady Widget")
    customer = seeder.customer(business.id, "Reliable Co")

    # A single recent, healthy-margin, paid-on-time sale and no prior-period
    # data at all. Every signal here is a period-over-period or overdue
    # comparison, and with nothing to compare against (previous revenue/
    # margin baseline is 0/absent), none of them should fire.
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=1, quantity=10, unit_price=100, cost_price=50)

    signals = detect_signals(db_session, business.id, date.today())
    assert signals == []


def test_detect_signals_combines_multiple_signal_types(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Acme Traders")

    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=45, quantity=1, unit_price=20000)
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=5, quantity=1, unit_price=5000)
    seeder.sale(business.id, customer_id=customer.id, total_amount=Decimal("10000"),
                paid_amount=Decimal("0"), due_days_ago=75)

    signals = detect_signals(db_session, business.id, date.today())
    codes = {s.code for s in signals}
    assert "CUSTOMER_REVENUE_DECLINE" in codes
    assert "RECEIVABLE_OVERDUE" in codes
