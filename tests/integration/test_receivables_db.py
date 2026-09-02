from decimal import Decimal

from packages.analytics.business_brain.metrics.receivables import (
    overdue_customers,
    receivables_summary,
)


def test_receivables_summary_buckets_overdue_amounts(db_session, seeder):
    business = seeder.business()
    # Overdue by 15 days -> 0_30 bucket.
    seeder.sale(business.id, total_amount=Decimal("1000"), paid_amount=Decimal("0"), due_days_ago=15)
    # Overdue by 70 days -> 61_90 bucket.
    seeder.sale(business.id, total_amount=Decimal("2000"), paid_amount=Decimal("500"), due_days_ago=70)
    # Not yet due.
    seeder.sale(business.id, total_amount=Decimal("500"), paid_amount=Decimal("0"), due_days_ago=-10)

    result = receivables_summary(db_session, business.id)
    assert result["outstanding"] == 1000.0 + 1500.0 + 500.0
    assert result["overdue"] == 1000.0 + 1500.0
    assert result["buckets"]["0_30"] == 1000.0
    assert result["buckets"]["61_90"] == 1500.0
    assert result["buckets"]["31_60"] == 0.0


def test_receivables_summary_excludes_fully_paid_invoices(db_session, seeder):
    business = seeder.business()
    seeder.sale(business.id, total_amount=Decimal("1000"), paid_amount=Decimal("1000"), due_days_ago=15)

    result = receivables_summary(db_session, business.id)
    assert result["outstanding"] == 0.0
    assert result["overdue"] == 0.0


def test_overdue_customers_reports_days_overdue_and_amount(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "ABC Electrical")
    seeder.sale(business.id, customer_id=customer.id, total_amount=Decimal("45000"),
                paid_amount=Decimal("0"), due_days_ago=75)

    result = overdue_customers(db_session, business.id)
    assert len(result) == 1
    assert result[0]["name"] == "ABC Electrical"
    assert result[0]["overdue_amount"] == 45000.0
    assert result[0]["days_overdue"] == 75


def test_overdue_customers_excludes_not_yet_due(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "Future Pay Co")
    seeder.sale(business.id, customer_id=customer.id, total_amount=Decimal("1000"),
                paid_amount=Decimal("0"), due_days_ago=-10)

    assert overdue_customers(db_session, business.id) == []


def test_overdue_customers_aggregates_multiple_invoices_per_customer(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "Repeat Offender Traders")
    seeder.sale(business.id, customer_id=customer.id, total_amount=Decimal("1000"),
                paid_amount=Decimal("0"), due_days_ago=10)
    seeder.sale(business.id, customer_id=customer.id, total_amount=Decimal("2000"),
                paid_amount=Decimal("0"), due_days_ago=40)

    result = overdue_customers(db_session, business.id)
    assert len(result) == 1
    assert result[0]["overdue_amount"] == 3000.0
    assert result[0]["days_overdue"] == 40  # the max of the two
