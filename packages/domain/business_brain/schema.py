"""Canonical business data contracts shared across ingestion and analytics."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class BusinessRecord(BaseModel):
    tenant_id: UUID
    source: str
    source_record_id: str
    ingested_at: datetime


class CustomerRecord(BusinessRecord):
    customer_id: UUID
    name: str
    phone: str | None = None
    email: str | None = None
    credit_limit: Decimal | None = Field(default=None, ge=0)


class ProductRecord(BusinessRecord):
    product_id: UUID
    sku: str | None = None
    name: str
    category: str | None = None
    unit: str | None = None


class SupplierRecord(BusinessRecord):
    supplier_id: UUID
    name: str
    phone: str | None = None
    email: str | None = None
    credit_period_days: int | None = Field(default=None, ge=0)


class SalesLineRecord(BusinessRecord):
    invoice_id: str
    customer_id: UUID | None = None
    product_id: UUID
    invoice_date: date
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount: Decimal = Field(default=0, ge=0)
    tax: Decimal = Field(default=0, ge=0)
    net_amount: Decimal = Field(ge=0)


class PurchaseLineRecord(BusinessRecord):
    purchase_id: str
    supplier_id: UUID | None = None
    product_id: UUID
    purchase_date: date
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    discount: Decimal = Field(default=0, ge=0)
    tax: Decimal = Field(default=0, ge=0)
    net_amount: Decimal = Field(ge=0)


class InventorySnapshotRecord(BusinessRecord):
    product_id: UUID
    snapshot_date: date
    quantity: Decimal = Field(ge=0)
    value: Decimal = Field(ge=0)


class InventoryMovementRecord(BusinessRecord):
    product_id: UUID
    movement_date: date
    movement_type: str
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    reference: str | None = None


class PaymentRecord(BusinessRecord):
    payment_id: str
    customer_id: UUID | None = None
    supplier_id: UUID | None = None
    sale_id: UUID | None = None
    purchase_id: UUID | None = None
    payment_date: date
    amount: Decimal = Field(gt=0)
    direction: str
    reference: str | None = None

    @model_validator(mode="after")
    def validate_direction(self) -> "PaymentRecord":
        if self.direction not in {"in", "out"}:
            raise ValueError("direction must be 'in' or 'out'")
        if self.customer_id is None and self.supplier_id is None:
            raise ValueError("payment must reference a customer or supplier")
        if self.customer_id is not None and self.supplier_id is not None:
            raise ValueError("payment cannot reference both customer and supplier")
        return self


class ExpenseRecord(BusinessRecord):
    expense_id: str
    expense_date: date
    category: str
    amount: Decimal = Field(gt=0)
    description: str | None = None
