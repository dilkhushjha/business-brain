from decimal import Decimal

from sqlalchemy import select

from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.shared.database.models import ProductModel, PurchaseLineModel, PurchaseModel, SupplierModel


def test_persist_purchases_creates_purchase_and_line(db_session, seeder):
    business = seeder.business()
    rows = [{
        "supplier_name": "ABC Distributors",
        "product_name": "LED Bulb 9W",
        "invoice_number": "PUR-1",
        "transaction_date": "27-08-2026",
        "quantity": "100",
        "unit_price": "60",
        "total_amount": "6000",
    }]

    created = persist_purchases(db_session, business.id, rows)
    db_session.commit()

    assert created == 1
    purchase = db_session.execute(select(PurchaseModel).where(PurchaseModel.business_id == business.id)).scalar_one()
    assert purchase.total_amount == Decimal("6000")
    supplier = db_session.execute(select(SupplierModel).where(SupplierModel.business_id == business.id)).scalar_one()
    assert supplier.name == "ABC Distributors"
    line = db_session.execute(select(PurchaseLineModel).where(PurchaseLineModel.purchase_id == purchase.id)).scalar_one()
    assert line.quantity == Decimal("100")
    assert line.unit_cost == Decimal("60")


def test_persist_purchases_creates_one_invoice_from_multiple_lines(db_session, seeder):
    business = seeder.business()
    rows = [
        {
            "supplier_name": "ABC Distributors", "product_name": "LED Bulb 9W",
            "invoice_number": "PUR-2", "transaction_date": "27-08-2026",
            "quantity": "10", "unit_price": "60", "total_amount": "600",
        },
        {
            "supplier_name": "ABC Distributors", "product_name": "MCB 32A",
            "invoice_number": "PUR-2", "transaction_date": "27-08-2026",
            "quantity": "5", "unit_price": "200", "total_amount": "1000",
        },
    ]

    created = persist_purchases(db_session, business.id, rows)
    db_session.commit()

    assert created == 1
    purchases = db_session.execute(select(PurchaseModel).where(PurchaseModel.business_id == business.id)).scalars().all()
    assert len(purchases) == 1
    lines = db_session.execute(select(PurchaseLineModel).where(PurchaseLineModel.purchase_id == purchases[0].id)).scalars().all()
    assert len(lines) == 2


def test_persist_purchases_reconciles_repeated_export(db_session, seeder):
    """Re-exporting the same invoice (e.g. now marked paid) should update
    the stored purchase, not create a duplicate or get silently skipped --
    mirrors persist_sales()'s reconciliation behavior."""
    business = seeder.business()
    first_pass = [{
        "supplier_name": "ABC Distributors", "product_name": "LED Bulb 9W",
        "invoice_number": "PUR-3", "transaction_date": "27-08-2026",
        "quantity": "10", "unit_price": "60", "total_amount": "600",
        "paid_amount": "0",
    }]
    persist_purchases(db_session, business.id, first_pass)
    db_session.commit()

    second_pass = [{
        "supplier_name": "ABC Distributors", "product_name": "LED Bulb 9W",
        "invoice_number": "PUR-3", "transaction_date": "27-08-2026",
        "quantity": "10", "unit_price": "60", "total_amount": "600",
        "paid_amount": "600",
    }]
    created = persist_purchases(db_session, business.id, second_pass)
    db_session.commit()

    assert created == 0  # reconciled, not counted as new
    purchases = db_session.execute(select(PurchaseModel).where(PurchaseModel.business_id == business.id)).scalars().all()
    assert len(purchases) == 1
    assert purchases[0].paid_amount == Decimal("600")


def test_persist_purchases_reuses_existing_supplier_and_product(db_session, seeder):
    business = seeder.business()
    seeder.supplier(business.id, "ABC Distributors")
    seeder.product(business.id, "LED Bulb 9W")

    rows = [{
        "supplier_name": "ABC Distributors", "product_name": "LED Bulb 9W",
        "invoice_number": "PUR-4", "transaction_date": "27-08-2026",
        "quantity": "1", "unit_price": "60", "total_amount": "60",
    }]
    persist_purchases(db_session, business.id, rows)
    db_session.commit()

    suppliers = db_session.execute(select(SupplierModel).where(SupplierModel.business_id == business.id)).scalars().all()
    products = db_session.execute(select(ProductModel).where(ProductModel.business_id == business.id)).scalars().all()
    assert len(suppliers) == 1
    assert len(products) == 1
