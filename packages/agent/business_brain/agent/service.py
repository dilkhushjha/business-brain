from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from packages.agent.business_brain.agent.context import retrieve_context
from packages.agent.business_brain.agent.intent import classify_intent
from packages.agent.business_brain.agent.models import AgentResponse
from packages.agent.business_brain.agent.responder import render_grounded_response


def answer(db: Session, business_id: UUID, question: str, as_of: date) -> AgentResponse:
    intent = classify_intent(question)
    context = retrieve_context(db, business_id, as_of)
    answer, confidence = render_grounded_response(question, intent, context)
    return AgentResponse(
        answer=answer,
        intent=intent,
        evidence=context.get("evidence", []),
        signals=context.get("signals", []),
        recommendations=context.get("recommendations", []),
        confidence=confidence,
    )
