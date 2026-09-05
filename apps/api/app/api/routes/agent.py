from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from apps.api.app.api.connector_auth import require_business_access
from packages.agent.business_brain.agent.service import answer
from packages.agent.business_brain.agent.explain import confidence_label, evidence_summary
from packages.shared.database.session import get_db
router=APIRouter(prefix="/agent",tags=["agent"])
class AgentQuestion(BaseModel):
    question:str
    as_of:date|None=None
@router.post("/{business_id}/ask")
def ask(business_id:UUID,request:AgentQuestion,db:Session=Depends(get_db),_auth:dict=Depends(require_business_access)):
    result=answer(db,business_id,request.question,request.as_of or date.today())
    return {"answer":result.answer,"intent":result.intent,"confidence":result.confidence,"confidence_label":confidence_label(result.confidence),"evidence":result.evidence,"evidence_summary":evidence_summary(result.evidence),"signals":result.signals,"recommendations":result.recommendations}
