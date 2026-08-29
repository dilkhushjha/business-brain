from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable

from .schema import FieldRule, ValidationIssue, validate_row


@dataclass(frozen=True)
class ValidationReport:
    rows_read: int
    rows_accepted: int
    rows_rejected: int
    duplicate_rows: int
    issues: list[ValidationIssue]

    def as_dict(self) -> dict[str, Any]:
        return {
            "rows_read": self.rows_read,
            "rows_accepted": self.rows_accepted,
            "rows_rejected": self.rows_rejected,
            "duplicate_rows": self.duplicate_rows,
            "issues": [issue.__dict__ for issue in self.issues],
        }


def _row_fingerprint(row: dict[str, Any]) -> str:
    payload = "|".join(
        f"{key}={str(row.get(key, '')).strip()}" for key in sorted(row)
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def validate_dataset(
    rows: Iterable[dict[str, Any]],
    rules: list[FieldRule],
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    accepted = rejected = duplicates = total = 0

    for row_number, row in enumerate(rows, start=1):
        total += 1
        fingerprint = _row_fingerprint(row)
        row_issues = validate_row(row, rules, row_number)

        if fingerprint in seen:
            duplicates += 1
            row_issues.append(
                ValidationIssue(
                    row_number,
                    None,
                    "DUPLICATE_ROW",
                    "Duplicate row detected",
                    severity="warning",
                )
            )
        else:
            seen.add(fingerprint)

        has_error = any(issue.severity == "error" for issue in row_issues)
        if has_error:
            rejected += 1
        else:
            accepted += 1
        issues.extend(row_issues)

    return ValidationReport(total, accepted, rejected, duplicates, issues)
