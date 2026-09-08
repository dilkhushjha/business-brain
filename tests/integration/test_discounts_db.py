from decimal import Decimal

from packages.analytics.business_brain.metrics.discounts import discount_anomalies


def test_discount_anomaly_flags_material_outlier(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "Regular Buyer")
    outlier = seeder.customer(business.id, "Big Discount Customer")

    # Baseline: several invoices around a 5% discount rate (50 discount on
    # a 950 net amount -> gross 1000, 5% discount rate).
    for _ in range(4):
        seeder.sale(business.id, customer_id=customer.id, days_ago=10,
                    total_amount=Decimal("950"), discount_amount=Decimal("50"))

    # One invoice with a much higher discount rate: 400 discount on a 600
    # net amount -> gross 1000, 40% discount rate.
    seeder.sale(business.id, customer_id=outlier.id, days_ago=10,
                total_amount=Decimal("600"), discount_amount=Decimal("400"))

    result = discount_anomalies(business_id=business.id, db=db_session)
    assert len(result) == 1
    assert result[0]["customer"] == "Big Discount Customer"
    assert result[0]["severity"] == "high"


def test_discount_anomaly_ignores_consistent_discounting(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "Regular Buyer")

    for _ in range(5):
        seeder.sale(business.id, customer_id=customer.id, days_ago=10,
                    total_amount=Decimal("950"), discount_amount=Decimal("50"))

    assert discount_anomalies(db_session, business.id) == []


def test_discount_anomaly_requires_a_real_baseline(db_session, seeder):
    """With only one or two discounted invoices, there's no real baseline
    to compare against -- shouldn't flag anything from noise."""
    business = seeder.business()
    customer = seeder.customer(business.id, "One Time Buyer")
    seeder.sale(business.id, customer_id=customer.id, days_ago=10,
                total_amount=Decimal("500"), discount_amount=Decimal("400"))

    assert discount_anomalies(db_session, business.id) == []


def test_discount_anomaly_ignores_negligible_baseline(db_session, seeder):
    """A baseline discount rate near zero (e.g. rounding/rebate dust)
    shouldn't make a merely-small real discount look like a 2x anomaly."""
    business = seeder.business()
    customer = seeder.customer(business.id, "Steady Buyer")
    for _ in range(4):
        seeder.sale(business.id, customer_id=customer.id, days_ago=10,
                    total_amount=Decimal("999"), discount_amount=Decimal("1"))

    assert discount_anomalies(db_session, business.id) == []


def test_discount_anomaly_excludes_undiscounted_invoices(db_session, seeder):
    """A sale with discount_amount == 0 shouldn't count toward the
    baseline or ever be flagged -- it never had a discount to be
    anomalous about."""
    business = seeder.business()
    customer = seeder.customer(business.id, "No Discount Buyer")
    for _ in range(5):
        seeder.sale(business.id, customer_id=customer.id, days_ago=10,
                    total_amount=Decimal("1000"), discount_amount=Decimal("0"))

    assert discount_anomalies(db_session, business.id) == []
