from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Supplier:
    id: UUID
    business_id: UUID
    name: str
    external_id: str | None = None
    phone: str | None = None
    email: str | None = None
    credit_period_days: int | None = None
