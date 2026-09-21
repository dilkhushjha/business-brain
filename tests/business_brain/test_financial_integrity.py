from packages.analytics.business_brain.financial_integrity import audit_financial_linkage
from packages.shared.database.models import PaymentModel


def test_financial_linkage_reconciles_document_and_payment_ledger(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "Customer")
    supplier = seeder.supplier(business.id, "Supplier")
    product = seeder.product(business.id, "Cable")
    sale = seeder.sale_with_line(business.id, product.id, quantity=2, unit_price=100)
    sale.customer_id = customer.id
    sale.paid_amount = 80
    purchase = seeder.purchase_with_line(
        business.id, product, quantity=2, unit_cost=50, invoice_number="PUR-FIN-1"
    )
    purchase.supplier_id = supplier.id
    purchase.paid_amount = 60
    db_session.add_all([
        PaymentModel(
            business_id=business.id, customer_id=customer.id, sale_id=sale.id,
            payment_date=sale.transaction_date, amount=80, direction="in"
        ),
        PaymentModel(
            business_id=business.id, supplier_id=supplier.id, purchase_id=purchase.id,
            payment_date=purchase.transaction_date, amount=60, direction="out"
        ),
    ])
    db_session.commit()

    result = audit_financial_linkage(db_session, business.id)

    assert result["status"] == "reconciled"
    assert result["summary"]["issue_count"] == 0


def test_financial_linkage_detects_payment_mismatch_and_unlinked_payment(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "Customer")
    product = seeder.product(business.id, "Cable")
    sale = seeder.sale_with_line(business.id, product.id, quantity=1, unit_price=100)
    sale.customer_id = customer.id
    sale.paid_amount = 100
    db_session.add(
        PaymentModel(
            business_id=business.id, customer_id=customer.id, sale_id=sale.id,
            payment_date=sale.transaction_date, amount=70, direction="in"
        )
    )
    db_session.add(
        PaymentModel(
            business_id=business.id, customer_id=customer.id,
            payment_date=sale.transaction_date, amount=20, direction="in"
        )
    )
    db_session.commit()

    result = audit_financial_linkage(db_session, business.id)

    assert result["status"] == "attention_required"
    assert result["summary"]["receivable_mismatch_count"] == 1
    assert result["summary"]["unlinked_payment_count"] == 1
