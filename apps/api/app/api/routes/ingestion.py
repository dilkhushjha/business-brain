from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.duplicate import already_imported
from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.ingestion.persistence import persist_ingestion_run
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.session import get_db

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xls"}


def _validate_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="A filename is required")
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    return suffix


@router.post("/preview/{business_id}")
def preview_ingestion(
    business_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    suffix = _validate_filename(file.filename)

    with NamedTemporaryFile(suffix=suffix, delete=True) as temp:
        temp.write(file.file.read())
        temp.flush()
        if already_imported(db, business_id, temp.name):
            raise HTTPException(status_code=409, detail="This source file was already imported")
        result, _ = prepare_file(temp.name, source_name=file.filename)

    return {
        "source": result.source.name,
        "checksum": result.source.checksum,
        "rows_read": result.rows_read,
        "rows_accepted": result.rows_accepted,
        "rows_rejected": result.rows_rejected,
        "issues": [issue.__dict__ for issue in result.issues[:100]],
    }


@router.post("/record-run/{business_id}")
def record_ingestion_run(
    business_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    suffix = _validate_filename(file.filename)

    with NamedTemporaryFile(suffix=suffix, delete=True) as temp:
        temp.write(file.file.read())
        temp.flush()
        if already_imported(db, business_id, temp.name):
            raise HTTPException(status_code=409, detail="This source file was already imported")

        result, prepared = prepare_file(temp.name, source_name=file.filename)
        run = persist_ingestion_run(db, business_id, result)
        created_sales = persist_sales(db, business_id, [row.values for row in prepared])

    return {
        "run_id": str(run.id),
        "status": run.status,
        "source": result.source.name,
        "rows_read": result.rows_read,
        "rows_accepted": result.rows_accepted,
        "rows_rejected": result.rows_rejected,
        "sales_created": created_sales,
    }
