from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class BusinessEntity:
    entity_type: str
    entity_id: UUID
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    source: str
    metric: str
    value: Decimal | None
    period: str | None
    dimension: str | None = None
    entity_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BusinessContext:
    business_id: UUID
    entities: list[BusinessEntity]
    evidence: list[Evidence]
    signals: list[Any]
    recommendations: list[Any]
