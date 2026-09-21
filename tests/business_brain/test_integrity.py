from datetime import date
from decimal import Decimal

from packages.analytics.business_brain.integrity import audit_inventory_integrity
from packages.shared.database.models import InventoryMovementModel


def movement(db, business_id, product_id, movement_type, quantity, reference):
    row = InventoryMovementModel(
        business_id=business_id,
        product_id=product_id,
        movement_date=date.today(),
        movement_type=movement_type,
        quantity=Decimal(str(quantity)),
        reference=reference,
    )
    db.add(row)
    db.commit()
    return row


def test_inventory_integrity_reports_reconciled_documents(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Cable")
    purchase = seeder.purchase_with_line(
        business.id, product.id, quantity=10, unit_cost=50, invoice_number="PUR-1"
    )
    sale = seeder.sale_with_line(
        business.id, product.id, quantity=4, unit_price=100
    )

    movement(db_session, business.id, product.id, "purchase", 10, purchase.invoice_number)
    movement(db_session, business.id, product.id, "sale", 4, sale.invoice_number)

    result = audit_inventory_integrity(db_session, business.id)

    assert result["status"] == "reconciled"
    assert result["summary"]["issue_count"] == 0


def test_inventory_integrity_detects_line_quantity_mismatch(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Cable")
    purchase = seeder.purchase_with_line(
        business.id, product.id, quantity=10, unit_cost=50, invoice_number="PUR-2"
    )

    movement(db_session, business.id, product.id, "purchase", 7, purchase.invoice_number)

    result = audit_inventory_integrity(db_session, business.id)

    assert result["status"] == "attention_required"
    assert result["summary"]["purchase_line_mismatch_count"] == 1
    assert result["purchase_line_mismatches"][0]["difference"] == -3.0


def test_inventory_integrity_detects_orphan_and_negative_balance(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Cable")

    movement(db_session, business.id, product.id, "sale", 5, "MISSING-INVOICE")

    result = audit_inventory_integrity(db_session, business.id)

    assert result["summary"]["orphan_movement_count"] == 1
    assert result["summary"]["negative_balance_count"] == 1
    assert result["status"] == "attention_required"
