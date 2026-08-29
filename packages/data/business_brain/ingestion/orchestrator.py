from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from datetime import datetime, timezone

from packages.data.business_brain.ingestion.models import IngestionIssue, IngestionResult, SourceFile
from packages.data.business_brain.ingestion.csv import CSVAdapter
from packages.data.business_brain.ingestion.excel import ExcelAdapter
from packages.data.business_brain.normalization.column_mapper import suggest_mapping
from packages.data.business_brain.validation.schema import FieldRule, validate_row


@dataclass(frozen=True)
class PreparedRow:
    row_number: int
    values: dict


def fingerprint(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _adapter(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return CSVAdapter()
    if suffix in {".xlsx", ".xls"}:
        return ExcelAdapter()
    raise ValueError(f"Unsupported source format: {suffix}")


def prepare_file(
    path: str | Path,
    *,
    source_name: str | None = None,
) -> tuple[IngestionResult, list[PreparedRow]]:
    """Read, map and validate a business export without writing to the database.

    ``source_name`` preserves the customer's original filename when the source is
    processed through a temporary upload file.
    """
    path = Path(path)
    adapter = _adapter(path)
    rows = adapter.ingest(path)
    mappings = suggest_mapping(list(rows[0].keys()) if rows else [])
    mapping = {item.source_column: item.canonical_field for item in mappings}

    prepared: list[PreparedRow] = []
    issues: list[IngestionIssue] = []
    rules = [
        FieldRule("invoice_number", required=True),
        FieldRule("transaction_date", required=True),
        FieldRule("quantity", kind="number"),
        FieldRule("unit_price", kind="number"),
        FieldRule("total_amount", kind="number"),
    ]

    for row_number, row in enumerate(rows, start=2):
        canonical = {mapping[key]: value for key, value in row.items() if key in mapping}
        row_issues = validate_row(canonical, rules, row_number)
        if row_issues:
            issues.extend(
                IngestionIssue(i.severity, i.code, i.message, i.row_number, i.field)
                for i in row_issues
            )
        else:
            prepared.append(PreparedRow(row_number, canonical))

    source = SourceFile(
        name=source_name or path.name,
        checksum=fingerprint(path),
        size_bytes=path.stat().st_size,
        imported_at=datetime.now(timezone.utc),
        metadata={"format": path.suffix.lower(), "column_mappings": mapping},
    )
    result = IngestionResult(
        source=source,
        rows_read=len(rows),
        rows_accepted=len(prepared),
        rows_rejected=len(rows) - len(prepared),
        issues=issues,
    )
    return result, prepared
