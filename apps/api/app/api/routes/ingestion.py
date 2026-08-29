from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from packages.data.business_brain.ingestion.duplicate import already_imported
from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.ingestion.persistence import persist_ingestion_run
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.data.business_brain.ingestion.column_mapping import suggest_mapping
from packages.shared.database.session import get_db
router=APIRouter(prefix="/ingestion",tags=["ingestion"]);SUPPORTED_SUFFIXES={".csv",".xlsx",".xls"}
def _validate_filename(filename:str|None)->str:
    if not filename: raise HTTPException(400,"A filename is required")
    suffix=Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES: raise HTTPException(400,"Only CSV and Excel files are supported")
    return suffix
def _prepare_upload(file:UploadFile,business_id:UUID,db:Session):
    suffix=_validate_filename(file.filename)
    temp=NamedTemporaryFile(suffix=suffix,delete=False)
    try:
        temp.write(file.file.read());temp.flush();temp.close()
        if already_imported(db,business_id,temp.name): raise HTTPException(409,"This source file was already imported")
        return prepare_file(temp.name,source_name=file.filename),temp.name
    except Exception:
        try:temp.close()
        finally:Path(temp.name).unlink(missing_ok=True)
        raise
@router.post("/preview/{business_id}")
def preview_ingestion(business_id:UUID,file:UploadFile=File(...),db:Session=Depends(get_db)):
    result,prepared=_prepare_upload(file,business_id,db)
    try:
        columns=list(prepared.values.keys()) if prepared else []
        return {"source":result.source.name,"checksum":result.source.checksum,"columns":columns,"mapping":[m.__dict__ for m in suggest_mapping(columns)],"rows_read":result.rows_read,"rows_accepted":result.rows_accepted,"rows_rejected":result.rows_rejected,"issues":[issue.__dict__ for issue in result.issues[:100]]}
    finally:Path(prepared).unlink(missing_ok=True)
@router.post("/import/{business_id}")
@router.post("/record-run/{business_id}")
def record_ingestion_run(business_id:UUID,file:UploadFile=File(...),db:Session=Depends(get_db)):
    result,temp_path=_prepare_upload(file,business_id,db)
    try:
        if result.rows_rejected: raise HTTPException(422,detail=f"Import blocked: {result.rows_rejected} row(s) failed validation")
        prepared=prepare_file(temp_path,source_name=file.filename)[1]
        run=persist_ingestion_run(db,business_id,result);created_sales=persist_sales(db,business_id,[row.values for row in prepared]);db.commit();db.refresh(run)
        return {"run_id":str(run.id),"status":run.status,"source":result.source.name,"checksum":result.source.checksum,"rows_read":result.rows_read,"rows_accepted":result.rows_accepted,"rows_rejected":result.rows_rejected,"sales_created":created_sales}
    except HTTPException: db.rollback();raise
    except Exception: db.rollback();raise HTTPException(500,"Import failed; no partial data was committed")
    finally:Path(temp_path).unlink(missing_ok=True)
