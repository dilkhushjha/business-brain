from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldRule:
    name: str
    required: bool = False
    kind: str = "text"


@dataclass(frozen=True)
class ValidationIssue:
    row_number: int
    field: str | None
    code: str
    message: str
    severity: str = "error"


def validate_row(row: dict[str, Any], rules: list[FieldRule], row_number: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rule in rules:
        value = row.get(rule.name)
        if rule.required and (value is None or str(value).strip() == ""):
            issues.append(ValidationIssue(row_number, rule.name, "REQUIRED", f"{rule.name} is required"))
            continue
        if value is None or value == "":
            continue
        if rule.kind == "number":
            try:
                float(str(value).replace(",", ""))
            except ValueError:
                issues.append(ValidationIssue(row_number, rule.name, "INVALID_NUMBER", f"Invalid number: {value}"))
    return issues
