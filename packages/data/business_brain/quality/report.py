from dataclasses import dataclass

from packages.data.business_brain.ingestion.models import IngestionResult


@dataclass(frozen=True)
class QualityReport:
    score: float
    rows_read: int
    rows_accepted: int
    rows_rejected: int
    error_count: int
    warnings: int


def build_quality_report(result: IngestionResult) -> QualityReport:
    denominator = max(result.rows_read, 1)
    acceptance = result.rows_accepted / denominator
    error_count = sum(1 for issue in result.issues if issue.severity == "error")
    warnings = sum(1 for issue in result.issues if issue.severity == "warning")
    score = round(max(0.0, acceptance * 100.0), 2)
    return QualityReport(score, result.rows_read, result.rows_accepted, result.rows_rejected, error_count, warnings)
