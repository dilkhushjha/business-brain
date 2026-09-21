from packages.analytics.business_brain.data_quality import audit_data_quality
from packages.shared.database.models import CustomerModel, ProductModel


def test_data_quality_reconciles_clean_business(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Cable")
    customer = seeder.customer(business.id, "Customer")
    sale = seeder.sale_with_line(business.id, product.id, quantity=2, unit_price=100)
    sale.customer_id = customer.id
    sale.total_amount = 200
    db_session.commit()

    result = audit_data_quality(db_session, business.id)

    assert result["status"] == "reconciled"
    assert result["summary"]["issue_count"] == 0


def test_data_quality_detects_ambiguous_entity_names(db_session, seeder):
    business = seeder.business()
    db_session.add_all([
        CustomerModel(business_id=business.id, name="Acme"),
        CustomerModel(business_id=business.id, name=" acme "),
        ProductModel(business_id=business.id, name="HDMI Cable"),
        ProductModel(business_id=business.id, name="hdmi  cable"),
    ])
    db_session.commit()

    result = audit_data_quality(db_session, business.id)

    assert result["status"] == "attention_required"
    assert result["summary"]["duplicate_entity_group_count"] == 2
    assert result["sections"]["customers"]["duplicate_name_groups"][0]["count"] == 2


def test_data_quality_detects_document_and_numeric_issues(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Cable")
    sale = seeder.sale_with_line(business.id, product.id, quantity=2, unit_price=100)
    sale.total_amount = 250
    line = sale.lines[0]
    line.quantity = 0
    db_session.commit()

    result = audit_data_quality(db_session, business.id)

    assert result["status"] == "attention_required"
    assert result["summary"]["document_total_mismatch_count"] == 1
    assert result["summary"]["numeric_issue_count"] == 1
