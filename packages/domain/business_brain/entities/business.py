from dataclasses import dataclass
from uuid import UUID
@dataclass(frozen=True)
class Business:
    id: UUID
    name: str
    industry: str
