"""Canonical business data contracts shared across ingestion and analytics."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


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
    credit_limit: Decimal | None = None


class ProductRecord(BusinessRecord):
    product_id: UUID
    sku: str | None = None
    name: str
    category: str | None = None
    unit: str | None = None


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
    net_amount: Decimal = Field(ge=0)


class InventorySnapshotRecord(BusinessRecord):
    product_id: UUID
    snapshot_date: date
    quantity: Decimal
    value: Decimal


class PaymentRecord(BusinessRecord):
    payment_id: str
    customer_id: UUID | None = None
    payment_date: date
    amount: Decimal = Field(gt=0)


class ExpenseRecord(BusinessRecord):
    expense_id: str
    expense_date: date
    category: str
    amount: Decimal = Field(gt=0)
