from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class Customer:
    id: UUID
    business_id: UUID
    name: str
    phone: str | None = None
    email: str | None = None
    credit_limit: Decimal | None = None
