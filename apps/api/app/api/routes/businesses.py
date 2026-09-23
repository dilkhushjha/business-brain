from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.app.api.routes.auth import get_current_user
from packages.shared.database.session import get_db

router = APIRouter(prefix="/businesses", tags=["businesses"])


class BusinessCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    industry: str = Field(min_length=2, max_length=64)


class BusinessUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    industry: str | None = Field(default=None, min_length=2, max_length=64)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    timezone: str | None = Field(default=None, min_length=3, max_length=64)
    fiscal_year_start_month: int | None = Field(default=None, ge=1, le=12)


class BusinessOnboardingRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    industry: str = Field(min_length=2, max_length=64)
    currency_code: str = Field(default="INR", min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    timezone: str = Field(default="Asia/Kolkata", min_length=3, max_length=64)
    fiscal_year_start_month: int = Field(default=4, ge=1, le=12)


def _business(row) -> dict:
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "industry": row["industry"],
        "role": row["role"],
        "currency_code": row["currency_code"],
        "timezone": row["timezone"],
        "fiscal_year_start_month": int(row["fiscal_year_start_month"]),
        "onboarding_completed": bool(row["onboarding_completed"]),
        "onboarding_completed_at": row["onboarding_completed_at"].isoformat() if row["onboarding_completed_at"] else None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


def _membership(db: Session, user_id: UUID, business_id: UUID):
    return db.execute(
        text("""
            SELECT b.id, b.name, b.industry, b.currency_code, b.timezone,
                   b.fiscal_year_start_month, b.onboarding_completed,
                   b.onboarding_completed_at, b.created_at, ub.role
            FROM user_businesses ub
            JOIN businesses b ON b.id = ub.business_id
            WHERE ub.user_id=:user_id AND ub.business_id=:business_id
            LIMIT 1
        """),
        {"user_id": user_id.hex, "business_id": business_id.hex},
    ).mappings().first()


@router.get("")
def list_businesses(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT b.id, b.name, b.industry, b.currency_code, b.timezone,
                   b.fiscal_year_start_month, b.onboarding_completed,
                   b.onboarding_completed_at, b.created_at, ub.role
            FROM user_businesses ub
            JOIN businesses b ON b.id = ub.business_id
            WHERE ub.user_id=:user_id
            ORDER BY ub.created_at
        """),
        {"user_id": str(user["id"])},
    ).mappings().all()
    return {"businesses": [_business(row) for row in rows]}


@router.post("", status_code=201)
def create_business(
    payload: BusinessCreateRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_id = uuid4()
    db.execute(
        text("""
            INSERT INTO businesses (id, name, industry, created_at)
            VALUES (:id, :name, :industry, CURRENT_TIMESTAMP)
        """),
        {
            "id": business_id.hex,
            "name": payload.name.strip(),
            "industry": payload.industry.strip().lower(),
        },
    )
    db.execute(
        text("""
            INSERT INTO user_businesses (user_id, business_id, role)
            VALUES (:user_id, :business_id, 'owner')
        """),
        {"user_id": str(user["id"]), "business_id": business_id.hex},
    )
    db.commit()
    row = _membership(db, UUID(str(user["id"])), business_id)
    return _business(row)


@router.get("/{business_id}")
def get_business(
    business_id: UUID,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _membership(db, UUID(str(user["id"])), business_id)
    if not row:
        raise HTTPException(404, "Business not found")
    return _business(row)


@router.post("/{business_id}/onboarding")
def complete_onboarding(
    business_id: UUID,
    payload: BusinessOnboardingRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _membership(db, UUID(str(user["id"])), business_id)
    if not row:
        raise HTTPException(404, "Business not found")
    if row["role"] != "owner":
        raise HTTPException(403, "Only the business owner can complete onboarding")

    db.execute(
        text("""
            UPDATE businesses
            SET name=:name,
                industry=:industry,
                currency_code=:currency_code,
                timezone=:timezone,
                fiscal_year_start_month=:fiscal_year_start_month,
                onboarding_completed=TRUE,
                onboarding_completed_at=CURRENT_TIMESTAMP
            WHERE id=:business_id
        """),
        {
            "name": payload.name.strip(),
            "industry": payload.industry.strip().lower(),
            "currency_code": payload.currency_code.strip().upper(),
            "timezone": payload.timezone.strip(),
            "fiscal_year_start_month": payload.fiscal_year_start_month,
            "business_id": business_id.hex,
        },
    )
    db.commit()
    return _business(_membership(db, UUID(str(user["id"])), business_id))


@router.patch("/{business_id}")
def update_business(
    business_id: UUID,
    payload: BusinessUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _membership(db, UUID(str(user["id"])), business_id)
    if not row:
        raise HTTPException(404, "Business not found")
    if row["role"] != "owner":
        raise HTTPException(403, "Only the business owner can update the business profile")

    updates: dict[str, str] = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.industry is not None:
        updates["industry"] = payload.industry.strip().lower()
    if payload.currency_code is not None:
        updates["currency_code"] = payload.currency_code.strip().upper()
    if payload.timezone is not None:
        updates["timezone"] = payload.timezone.strip()
    if payload.fiscal_year_start_month is not None:
        updates["fiscal_year_start_month"] = str(payload.fiscal_year_start_month)
    if not updates:
        return _business(row)

    db.execute(
        text("""
            UPDATE businesses
            SET name=COALESCE(:name, name),
                industry=COALESCE(:industry, industry),
                currency_code=COALESCE(:currency_code, currency_code),
                timezone=COALESCE(:timezone, timezone),
                fiscal_year_start_month=COALESCE(:fiscal_year_start_month, fiscal_year_start_month)
            WHERE id=:business_id
        """),
        {
            "name": updates.get("name"),
            "industry": updates.get("industry"),
            "currency_code": updates.get("currency_code"),
            "timezone": updates.get("timezone"),
            "fiscal_year_start_month": updates.get("fiscal_year_start_month"),
            "business_id": business_id.hex,
        },
    )
    db.commit()
    return _business(_membership(db, UUID(str(user["id"])), business_id))
