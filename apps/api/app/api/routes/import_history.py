from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from packages.shared.database.models import IngestionRunModel, SourceFileModel
from packages.shared.database.session import get_db
router=APIRouter(prefix="/imports",tags=["ingestion"])
@router.get("/{business_id}/history")
def history(business_id:UUID,limit:int=20,db:Session=Depends(get_db)):
    limit=max(1,min(limit,100)); rows=db.execute(select(IngestionRunModel,SourceFileModel).join(SourceFileModel,SourceFileModel.id==IngestionRunModel.source_file_id).where(IngestionRunModel.business_id==business_id).order_by(IngestionRunModel.started_at.desc()).limit(limit)).all()
    return [{"run_id":str(run.id),"file_name":source.name,"checksum":source.checksum,"status":run.status,"rows_read":run.rows_read,"rows_accepted":run.rows_accepted,"rows_rejected":run.rows_rejected,"started_at":run.started_at.isoformat(),"completed_at":run.completed_at.isoformat() if run.completed_at else None} for run,source in rows]
