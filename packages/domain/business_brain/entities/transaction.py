from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class Sale:
    id: UUID
    business_id: UUID
    customer_id: UUID | None
    transaction_date: date
    invoice_number: str
    total_amount: Decimal
    tax_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    due_date: date | None = None
    paid_amount: Decimal = Decimal("0")


@dataclass(frozen=True)
class SaleLine:
    id: UUID
    sale_id: UUID
    product_id: UUID
    quantity: Decimal
    unit_price: Decimal
    cost_price: Decimal | None = None


@dataclass(frozen=True)
class Purchase:
    id: UUID
    business_id: UUID
    supplier_id: UUID | None
    transaction_date: date
    invoice_number: str
    total_amount: Decimal
    tax_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    due_date: date | None = None
    paid_amount: Decimal = Decimal("0")


@dataclass(frozen=True)
class PurchaseLine:
    id: UUID
    purchase_id: UUID
    product_id: UUID
    quantity: Decimal
    unit_cost: Decimal
    tax_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    net_amount: Decimal | None = None


@dataclass(frozen=True)
class Payment:
    id: UUID
    business_id: UUID
    payment_date: date
    amount: Decimal
    direction: str
    customer_id: UUID | None = None
    supplier_id: UUID | None = None
    sale_id: UUID | None = None
    purchase_id: UUID | None = None
    reference: str | None = None


@dataclass(frozen=True)
class Expense:
    id: UUID
    business_id: UUID
    expense_date: date
    category: str
    amount: Decimal
    external_id: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class InventorySnapshot:
    id: UUID
    business_id: UUID
    product_id: UUID
    snapshot_date: date
    quantity: Decimal
    value: Decimal


@dataclass(frozen=True)
class InventoryMovement:
    id: UUID
    business_id: UUID
    product_id: UUID
    movement_date: date
    movement_type: str
    quantity: Decimal
    unit_cost: Decimal | None = None
    reference: str | None = None
