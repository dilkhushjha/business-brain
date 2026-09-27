from datetime import date
from uuid import uuid4

from packages.analytics.business_brain.pilot_readiness import audit_pilot_readiness
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
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
    persist_purchases(
        db_session,
        business.id,
        [{
            "invoice_number": "PILOT-PUR-001",
            "transaction_date": "2026-09-20",
            "product_name": product.name,
            "supplier_name": "Supplier",
            "quantity": 10,
            "unit_price": 50,
            "total_amount": 500,
        }],
    )
    persist_sales(
        db_session,
        business.id,
        [{
            "invoice_number": "PILOT-001",
            "transaction_date": "2026-09-22",
            "product_name": product.name,
            "customer_name": "Customer",
            "quantity": 2,
            "unit_price": 100,
            "total_amount": 200,
        }],
    )
    db_session.commit()

    result = audit_pilot_readiness(db_session, business.id, date(2026, 9, 22))

    assert result["status"] in {"ready", "ready_with_warnings"}
    assert not result["blockers"]
    assert result["counts"]["sales"] == 1


def test_pilot_readiness_warns_when_sales_history_is_stale(db_session, seeder):
    business = seeder.business(name="Pilot Stale", industry="retail")
    product = seeder.product(business.id, "Cable")
    seeder.sale_with_line(business.id, product.id, days_ago=120, quantity=2, unit_price=100)
    db_session.commit()

    result = audit_pilot_readiness(db_session, business.id, date.today())

    assert "STALE_SALES_DATA" in result["warnings"]
    freshness = next(check for check in result["checks"] if check["code"] == "STALE_SALES_DATA")
    assert freshness["age_days"] == 120
    assert freshness["threshold_days"] == 90
