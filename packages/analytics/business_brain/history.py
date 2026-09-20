from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.shared.database.models import BusinessSituationHistoryModel


@dataclass(frozen=True)
class SituationHistory:
    situation_code: str
    status: str
    trend: str
    first_seen_at: date
    last_seen_at: date
    resolved_at: date | None
    severity: str
    priority_score: Decimal
    confidence: Decimal
    title: str
    explanation: str
    evidence: dict[str, Any]


def _trend(previous: Decimal | None, current: Decimal) -> str:
    if previous is None:
        return "new"
    delta = current - previous
    if delta >= Decimal("5"):
        return "worsening"
    if delta <= Decimal("-5"):
        return "improving"
    return "stable"


def record_situation_history(
    db: Session,
    business_id: UUID,
    as_of: date,
    situations: list[Any],
    priorities: list[Any],
) -> list[SituationHistory]:
    """Persist the current situation state and mark disappeared situations resolved."""
    priority_by_code = {
        str(getattr(item, "situation_code", "")): item
        for item in priorities
    }
    current_codes = {str(getattr(item, "code", "")) for item in situations}

    existing = {
        row.situation_code: row
        for row in db.scalars(
            select(BusinessSituationHistoryModel).where(
                BusinessSituationHistoryModel.business_id == business_id
            )
        ).all()
    }

    results: list[SituationHistory] = []

    for situation in situations:
        code = str(getattr(situation, "code", ""))
        if not code:
            continue

        priority = priority_by_code.get(code)
        score = Decimal(str(getattr(priority, "score", "0")))
        confidence = Decimal(str(getattr(situation, "confidence", "0")))
        row = existing.get(code)

        if row is None:
            row = BusinessSituationHistoryModel(
                business_id=business_id,
                situation_code=code,
                first_seen_at=as_of,
                last_seen_at=as_of,
                resolved_at=None,
                status="active",
                severity=str(getattr(situation, "severity", "info")),
                priority_score=score,
                confidence=confidence,
                last_title=str(getattr(situation, "title", code)),
                last_explanation=str(getattr(situation, "explanation", "")),
                last_evidence=dict(getattr(situation, "evidence", {}) or {}),
            )
            db.add(row)
            trend = "new"
        else:
            trend = _trend(Decimal(str(row.priority_score)), score)
            if as_of >= row.last_seen_at:
                row.last_seen_at = as_of
                row.resolved_at = None
                row.status = "active"
                row.severity = str(getattr(situation, "severity", row.severity))
                row.priority_score = score
                row.confidence = confidence
                row.last_title = str(getattr(situation, "title", code))
                row.last_explanation = str(getattr(situation, "explanation", ""))
                row.last_evidence = dict(getattr(situation, "evidence", {}) or {})

        results.append(SituationHistory(
            situation_code=code,
            status="active",
            trend=trend,
            first_seen_at=row.first_seen_at,
            last_seen_at=as_of if as_of >= row.last_seen_at else row.last_seen_at,
            resolved_at=None,
            severity=str(getattr(situation, "severity", "info")),
            priority_score=score,
            confidence=confidence,
            title=str(getattr(situation, "title", code)),
            explanation=str(getattr(situation, "explanation", "")),
            evidence=dict(getattr(situation, "evidence", {}) or {}),
        ))

    for code, row in existing.items():
        if code in current_codes or row.status == "resolved":
            continue
        if as_of < row.last_seen_at:
            continue
        row.status = "resolved"
        row.resolved_at = as_of
        results.append(SituationHistory(
            situation_code=code,
            status="resolved",
            trend="resolved",
            first_seen_at=row.first_seen_at,
            last_seen_at=row.last_seen_at,
            resolved_at=as_of,
            severity=row.severity,
            priority_score=Decimal(str(row.priority_score)),
            confidence=Decimal(str(row.confidence)),
            title=row.last_title,
            explanation=row.last_explanation,
            evidence=dict(row.last_evidence or {}),
        ))

    # Situation history is an intentional durable side effect of refreshing Business Brain.
    db.commit()
    return sorted(results, key=lambda item: (-item.priority_score, item.situation_code))


def load_situation_history(db: Session, business_id: UUID) -> list[SituationHistory]:
    rows = db.scalars(
        select(BusinessSituationHistoryModel)
        .where(BusinessSituationHistoryModel.business_id == business_id)
        .order_by(BusinessSituationHistoryModel.last_seen_at.desc())
    ).all()

    return [
        SituationHistory(
            situation_code=row.situation_code,
            status=row.status,
            trend="resolved" if row.status == "resolved" else "stable",
            first_seen_at=row.first_seen_at,
            last_seen_at=row.last_seen_at,
            resolved_at=row.resolved_at,
            severity=row.severity,
            priority_score=Decimal(str(row.priority_score)),
            confidence=Decimal(str(row.confidence)),
            title=row.last_title,
            explanation=row.last_explanation,
            evidence=dict(row.last_evidence or {}),
        )
        for row in rows
    ]
