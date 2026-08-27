from dataclasses import dataclass
from uuid import UUID
@dataclass(frozen=True)
class Supplier:
    id: UUID
    business_id: UUID
    name: str
