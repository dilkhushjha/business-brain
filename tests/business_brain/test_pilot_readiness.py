from datetime import date
from uuid import uuid4

from packages.analytics.business_brain.pilot_readiness import audit_pilot_readiness
from packages.shared.database.models import BusinessModel


def test_pilot_readiness_blocks_business_without_sales(db_session):
    business = BusinessModel(id=uuid4(), name="Pilot Empty", industry="retail")
    db_session.add(business)
    db_session.commit()

    result = audit_pilot_readiness(db_session, business.id, date(2026, 9, 22))

    assert result["status"] == "not_ready"
    assert "NO_SALES_DATA" in result["blockers"]


def test_pilot_readiness_accepts_reconciled_sales_business(db_session, seeder):
    business = seeder.business(name="Pilot Ready", industry="distribution")
    product = seeder.product(business.id, "Cable")
    seeder.customer(business.id, "Customer")
    seeder.supplier(business.id, "Supplier")
    seeder.sale_with_line(
        business.id,
        product.id,
        quantity=2,
        unit_price=100,
    )
    db_session.commit()

    result = audit_pilot_readiness(db_session, business.id, date(2026, 9, 22))

    assert result["status"] in {"ready", "ready_with_warnings"}
    assert not result["blockers"]
    assert result["counts"]["sales"] == 1
