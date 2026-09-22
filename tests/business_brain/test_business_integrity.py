from packages.analytics.business_brain.business_integrity import audit_business_integrity


def test_business_integrity_reconciled_for_clean_business(db_session, seeder):
    business = seeder.business()
    result = audit_business_integrity(db_session, business.id)

    assert result["status"] == "reconciled"
    assert result["issue_count"] == 0
    assert result["affected_domains"] == []


def test_business_integrity_surfaces_data_quality_issues(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Cable")
    sale = seeder.sale_with_line(business.id, product, quantity=2, unit_price=100)
    sale.total_amount = 250
    db_session.commit()

    result = audit_business_integrity(db_session, business.id)

    assert result["status"] == "attention_required"
    assert "data_quality" in result["affected_domains"]
    assert result["issue_count"] >= 1
    assert "unresolved data-integrity issues" in result["conclusion_note"]


def test_business_integrity_is_read_only(db_session, seeder):
    business = seeder.business()
    before = db_session.query(type(business)).count()

    audit_business_integrity(db_session, business.id)

    after = db_session.query(type(business)).count()
    assert after == before
