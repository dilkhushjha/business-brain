from datetime import date, timedelta

from packages.analytics.business_brain.metrics.payables import overdue_suppliers, payables_summary
from packages.analytics.business_brain.metrics.receivables import overdue_customers, receivables_summary


def test_financial_aging_uses_supplied_as_of_date(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "Customer")
    supplier = seeder.supplier(business.id, "Supplier")
    product = seeder.product(business.id, "Cable")

    sale = seeder.sale_with_line(
        business.id, product, quantity=1, unit_price=100,
        due_days_ago=20,
    )
    sale.customer_id = customer.id
    sale.paid_amount = 0

    purchase = seeder.purchase_with_line(
        business.id, product, quantity=1, unit_cost=50,
        due_days_ago=20,
    )
    purchase.supplier_id = supplier.id
    purchase.paid_amount = 0
    db_session.commit()

    as_of = date.today()

    assert receivables_summary(db_session, business.id, as_of)["overdue"] == 100.0
    assert payables_summary(db_session, business.id, as_of)["overdue"] == 50.0
    assert overdue_customers(db_session, business.id, as_of=as_of)[0]["days_overdue"] == 19
    assert overdue_suppliers(db_session, business.id, as_of=as_of)[0]["days_overdue"] == 19

    # A future as-of date moves the same documents deeper into aging,
    # proving the business context is reproducible for historical dates.
    later = as_of + timedelta(days=11)
    assert overdue_customers(db_session, business.id, as_of=later)[0]["days_overdue"] == 30
    assert overdue_suppliers(db_session, business.id, as_of=later)[0]["days_overdue"] == 30
