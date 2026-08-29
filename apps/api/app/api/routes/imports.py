from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from packages.shared.database.models import SourceFileModel
from packages.shared.database.session import get_db
router=APIRouter(prefix="/imports",tags=["ingestion"])
@router.get("/{business_id}")
def import_history(business_id:UUID,limit:int=20,db:Session=Depends(get_db)):
    limit=max(1,min(limit,100))
    rows=db.execute(select(SourceFileModel).where(SourceFileModel.business_id==business_id).order_by(SourceFileModel.imported_at.desc()).limit(limit)).scalars().all()
    return [{"id":str(x.id),"name":x.name,"checksum":x.checksum,"size_bytes":x.size_bytes,"imported_at":x.imported_at.isoformat() if x.imported_at else None} for x in rows]
