from dataclasses import dataclass
@dataclass(frozen=True)
class Recommendation:
    action: str
    rationale: str
    confidence: float
