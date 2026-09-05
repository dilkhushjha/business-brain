from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.domain.business_brain.schema import (
    ExpenseRecord,
    InventoryMovementRecord,
    InventorySnapshotRecord,
    PaymentRecord,
    ProductRecord,
    PurchaseLineRecord,
    SupplierRecord,
)


@pytest.fixture
def base_fields() -> dict:
    return {
        "tenant_id": uuid4(),
        "source": "tally",
        "source_record_id": "row-1",
        "ingested_at": datetime(2026, 9, 5, 10, 0),
    }


def test_supplier_record_captures_counterparty_metadata(base_fields):
    record = SupplierRecord(
        **base_fields,
        supplier_id=uuid4(),
        name="ACME Electricals",
        credit_period_days=30,
    )

    assert record.name == "ACME Electricals"
    assert record.credit_period_days == 30


def test_purchase_line_supports_procurement_economics(base_fields):
    record = PurchaseLineRecord(
        **base_fields,
        purchase_id="PUR-001",
        supplier_id=uuid4(),
        product_id=uuid4(),
        purchase_date=date(2026, 9, 1),
        quantity=Decimal("10"),
        unit_cost=Decimal("125.50"),
        discount=Decimal("5"),
        tax=Decimal("21.69"),
        net_amount=Decimal("1271.69"),
    )

    assert record.quantity == Decimal("10")
    assert record.net_amount == Decimal("1271.69")


def test_inventory_snapshot_rejects_negative_stock(base_fields):
    with pytest.raises(ValidationError):
        InventorySnapshotRecord(
            **base_fields,
            product_id=uuid4(),
            snapshot_date=date(2026, 9, 5),
            quantity=Decimal("-1"),
            value=Decimal("0"),
        )


def test_inventory_movement_requires_positive_quantity(base_fields):
    with pytest.raises(ValidationError):
        InventoryMovementRecord(
            **base_fields,
            product_id=uuid4(),
            movement_date=date(2026, 9, 5),
            movement_type="purchase",
            quantity=Decimal("0"),
        )


def test_payment_requires_exactly_one_counterparty(base_fields):
    with pytest.raises(ValidationError):
        PaymentRecord(
            **base_fields,
            payment_id="PAY-001",
            payment_date=date(2026, 9, 5),
            amount=Decimal("1000"),
            direction="in",
        )

    with pytest.raises(ValidationError):
        PaymentRecord(
            **base_fields,
            payment_id="PAY-002",
            customer_id=uuid4(),
            supplier_id=uuid4(),
            payment_date=date(2026, 9, 5),
            amount=Decimal("1000"),
            direction="in",
        )


def test_payment_accepts_customer_or_supplier_payment(base_fields):
    customer_payment = PaymentRecord(
        **base_fields,
        payment_id="PAY-001",
        customer_id=uuid4(),
        payment_date=date(2026, 9, 5),
        amount=Decimal("1000"),
        direction="in",
    )
    supplier_payment = PaymentRecord(
        **base_fields,
        payment_id="PAY-002",
        supplier_id=uuid4(),
        payment_date=date(2026, 9, 5),
        amount=Decimal("750"),
        direction="out",
    )

    assert customer_payment.direction == "in"
    assert supplier_payment.direction == "out"


def test_expense_requires_positive_amount(base_fields):
    with pytest.raises(ValidationError):
        ExpenseRecord(
            **base_fields,
            expense_id="EXP-001",
            expense_date=date(2026, 9, 5),
            category="Rent",
            amount=Decimal("0"),
        )


def test_product_contract_includes_unit(base_fields):
    record = ProductRecord(
        **base_fields,
        product_id=uuid4(),
        sku="WIRE-001",
        name="Copper Wire",
        category="Electrical",
        unit="meter",
    )

    assert record.unit == "meter"
