from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.models import IngestionResult
from packages.shared.database.models import IngestionRunModel, SourceFileModel


def persist_ingestion_run(db: Session, business_id: UUID, result: IngestionResult) -> IngestionRunModel:
    """Stage the source file and ingestion run in the current transaction.

    The caller commits after all business rows have been persisted so a failed
    import cannot leave an apparently completed run behind.
    """
    source = SourceFileModel(
        business_id=business_id,
        name=result.source.name,
        checksum=result.source.checksum,
        size_bytes=result.source.size_bytes,
        imported_at=result.source.imported_at.replace(tzinfo=None),
    )
    db.add(source)
    db.flush()

    run = IngestionRunModel(
        business_id=business_id,
        source_file_id=source.id,
        status="completed" if result.rows_rejected == 0 else "completed_with_errors",
        rows_read=result.rows_read,
        rows_accepted=result.rows_accepted,
        rows_rejected=result.rows_rejected,
        error_summary="; ".join(issue.message for issue in result.issues[:20]) or None,
        started_at=result.source.imported_at.replace(tzinfo=None),
        completed_at=result.source.imported_at.replace(tzinfo=None),
    )
    db.add(run)
    db.flush()
    return run
