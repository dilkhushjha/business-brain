from dataclasses import dataclass
from uuid import UUID
@dataclass(frozen=True)
class Customer:
    id: UUID
    business_id: UUID
    name: str
