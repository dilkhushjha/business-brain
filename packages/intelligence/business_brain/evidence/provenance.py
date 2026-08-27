from dataclasses import dataclass
@dataclass(frozen=True)
class Evidence:
    source: str
    record_ids: tuple[str, ...]
    facts: dict
    calculation: str | None = None
