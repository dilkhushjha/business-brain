from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.orchestrator import fingerprint
from packages.shared.database.models import SourceFileModel


def already_imported(db: Session, business_id, path: str | Path) -> bool:
    checksum = fingerprint(Path(path))
    stmt = select(SourceFileModel.id).where(
        SourceFileModel.business_id == business_id,
        SourceFileModel.checksum == checksum,
    )
    return db.execute(stmt).scalar_one_or_none() is not None
