from dataclasses import dataclass
from uuid import UUID
@dataclass(frozen=True)
class Product:
    id: UUID
    business_id: UUID
    name: str
    sku: str | None = None
