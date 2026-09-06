from decimal import Decimal

from packages.analytics.business_brain.metrics.payables import (
    overdue_suppliers,
    payables_summary,
)


def test_payables_summary_buckets_overdue_amounts(db_session, seeder):
    business = seeder.business()
    # Overdue by 15 days -> 0_30 bucket.
    seeder.purchase(business.id, total_amount=Decimal("1000"), paid_amount=Decimal("0"), due_days_ago=15)
    # Overdue by 70 days -> 61_90 bucket.
    seeder.purchase(business.id, total_amount=Decimal("2000"), paid_amount=Decimal("500"), due_days_ago=70)
    # Not yet due.
    seeder.purchase(business.id, total_amount=Decimal("500"), paid_amount=Decimal("0"), due_days_ago=-10)

    result = payables_summary(db_session, business.id)
    assert result["outstanding"] == 1000.0 + 1500.0 + 500.0
    assert result["overdue"] == 1000.0 + 1500.0
    assert result["buckets"]["0_30"] == 1000.0
    assert result["buckets"]["61_90"] == 1500.0
    assert result["buckets"]["31_60"] == 0.0


def test_payables_summary_excludes_fully_paid_invoices(db_session, seeder):
    business = seeder.business()
    seeder.purchase(business.id, total_amount=Decimal("1000"), paid_amount=Decimal("1000"), due_days_ago=15)

    result = payables_summary(db_session, business.id)
    assert result["outstanding"] == 0.0
    assert result["overdue"] == 0.0


def test_overdue_suppliers_reports_days_overdue_and_amount(db_session, seeder):
    business = seeder.business()
    supplier = seeder.supplier(business.id, "ABC Distributors")
    seeder.purchase(business.id, supplier_id=supplier.id, total_amount=Decimal("45000"),
                     paid_amount=Decimal("0"), due_days_ago=75)

    result = overdue_suppliers(db_session, business.id)
    assert len(result) == 1
    assert result[0]["name"] == "ABC Distributors"
    assert result[0]["overdue_amount"] == 45000.0
    assert result[0]["days_overdue"] == 75


def test_overdue_suppliers_excludes_not_yet_due(db_session, seeder):
    business = seeder.business()
    supplier = seeder.supplier(business.id, "Future Pay Distributors")
    seeder.purchase(business.id, supplier_id=supplier.id, total_amount=Decimal("1000"),
                     paid_amount=Decimal("0"), due_days_ago=-10)

    assert overdue_suppliers(db_session, business.id) == []


def test_overdue_suppliers_aggregates_multiple_invoices_per_supplier(db_session, seeder):
    business = seeder.business()
    supplier = seeder.supplier(business.id, "Repeat Supplier Traders")
    seeder.purchase(business.id, supplier_id=supplier.id, total_amount=Decimal("1000"),
                     paid_amount=Decimal("0"), due_days_ago=10)
    seeder.purchase(business.id, supplier_id=supplier.id, total_amount=Decimal("2000"),
                     paid_amount=Decimal("0"), due_days_ago=40)

    result = overdue_suppliers(db_session, business.id)
    assert len(result) == 1
    assert result[0]["overdue_amount"] == 3000.0
    assert result[0]["days_overdue"] == 40  # the max of the two
