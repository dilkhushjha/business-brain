from packages.analytics.business_brain.readiness import build_business_readiness


def test_readiness_is_ready_for_clean_transaction_business(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Cable")
    seeder.sale_with_line(business.id, product.id, quantity=2, unit_price=100)

    result = build_business_readiness(db_session, business.id)

    assert result["status"] == "ready"
    assert result["transaction_coverage"]["sales_count"] == 1
    assert "sales" in result["domains_present"]
    assert result["integrity"]["status"] == "reconciled"


def test_readiness_requires_review_when_integrity_has_exceptions(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Cable")
    sale = seeder.sale_with_line(business.id, product.id, quantity=2, unit_price=100)
    sale.total_amount = 250
    db_session.commit()

    result = build_business_readiness(db_session, business.id)

    assert result["status"] == "review_required"
    assert result["integrity"]["issue_count"] >= 1
    assert "data_quality" in result["integrity"]["affected_domains"]


def test_readiness_reports_insufficient_data_for_empty_business(db_session, seeder):
    business = seeder.business()

    result = build_business_readiness(db_session, business.id)

    assert result["status"] == "insufficient_data"
    assert result["transaction_coverage"]["sales_count"] == 0
    assert result["transaction_coverage"]["purchase_count"] == 0
    assert result["limitations"]
