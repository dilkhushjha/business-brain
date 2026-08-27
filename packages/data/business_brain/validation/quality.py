from dataclasses import dataclass
@dataclass(frozen=True)
class DataQualityReport:
    score: float
    errors: int
    warnings: int
    rows_checked: int
