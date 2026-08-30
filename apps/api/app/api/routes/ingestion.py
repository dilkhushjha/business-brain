from os import close
from pathlib import Path
from tempfile import mkstemp
from uuid import UUID, uuid4
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.column_mapping import suggest_mapping
from packages.data.business_brain.ingestion.duplicate import already_imported
from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.ingestion.persistence import persist_ingestion_run
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.session import get_db

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
logger = logging.getLogger(__name__)
SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xls"}


def _validate_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(400, "A filename is required")
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(400, "Only CSV and Excel files are supported")
    return suffix


def _prepare_upload(file: UploadFile, business_id: UUID, db: Session):
    suffix = _validate_filename(file.filename)
    fd, temp_name = mkstemp(suffix=suffix)
    path = Path(temp_name)
    try:
        try:
            with path.open("wb") as stream:
                stream.write(file.file.read())
        finally:
            close(fd)

        if already_imported(db, business_id, path):
            raise HTTPException(409, "This source file was already imported")

        result, prepared = prepare_file(path, source_name=file.filename)
        return result, prepared, temp_name
    except Exception:
        path.unlink(missing_ok=True)
        raise


@router.post("/preview/{business_id}")
def preview_ingestion(
    business_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    result, prepared, temp_path = _prepare_upload(file, business_id, db)
    try:
        columns = list(prepared[0].values.keys()) if prepared else []
        return {
            "source": result.source.name,
            "checksum": result.source.checksum,
            "columns": columns,
            "mapping": [m.__dict__ for m in suggest_mapping(columns)],
            "rows_read": result.rows_read,
            "rows_accepted": result.rows_accepted,
            "rows_rejected": result.rows_rejected,
            "issues": [issue.__dict__ for issue in result.issues[:100]],
        }
    finally:
        Path(temp_path).unlink(missing_ok=True)


@router.post("/import/{business_id}")
@router.post("/record-run/{business_id}")
def record_ingestion_run(
    business_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())
    result, prepared, temp_path = _prepare_upload(file, business_id, db)
    try:
        if result.rows_rejected:
            raise HTTPException(
                422,
                detail=f"Import blocked: {result.rows_rejected} row(s) failed validation",
            )

        logger.info(
            "Starting ingestion request=%s business=%s source=%s rows=%s",
            request_id, business_id, result.source.name, result.rows_accepted,
        )
        run = persist_ingestion_run(db, business_id, result)
        created_sales = persist_sales(db, business_id, [row.values for row in prepared])
        db.commit()
        db.refresh(run)
        return {
            "run_id": str(run.id),
            "status": run.status,
            "source": result.source.name,
            "checksum": result.source.checksum,
            "rows_read": result.rows_read,
            "rows_accepted": result.rows_accepted,
            "rows_rejected": result.rows_rejected,
            "sales_created": created_sales,
            "request_id": request_id,
        }
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        logger.exception("Ingestion integrity failure request=%s business=%s", request_id, business_id)
        raise HTTPException(
            409,
            detail=f"Import could not be saved because the source or one of its business records already exists. No partial data was committed. Request: {request_id}",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Ingestion failure request=%s business=%s", request_id, business_id)
        detail = str(exc).strip() or "The database operation returned no diagnostic message. Check the backend traceback."
        raise HTTPException(
            500,
            detail=f"Import failed; no partial data was committed. {type(exc).__name__}: {detail} Request: {request_id}",
        ) from exc
    finally:
        Path(temp_path).unlink(missing_ok=True)
