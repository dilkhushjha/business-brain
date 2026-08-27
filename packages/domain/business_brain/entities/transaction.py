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


@dataclass(frozen=True)
class PurchaseLine:
    id: UUID
    purchase_id: UUID
    product_id: UUID
    quantity: Decimal
    unit_cost: Decimal
