from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    row: int
    field: str
    code: str
    message: str
    severity: str = "error"


REQUIRED_FIELDS = {"date", "amount"}


def validate_records(records: list[dict[str, Any]], mapped_fields: dict[str, str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = REQUIRED_FIELDS - set(mapped_fields.values())
    for field in sorted(missing):
        issues.append(ValidationIssue(0, field, "missing_mapping", f"Required field '{field}' has no source column."))

    for index, record in enumerate(records, start=1):
        for source, target in mapped_fields.items():
            value = record.get(source)
            if target in REQUIRED_FIELDS and value in (None, ""):
                issues.append(ValidationIssue(index, target, "missing_value", f"Required value for '{target}' is empty."))
    return issues
