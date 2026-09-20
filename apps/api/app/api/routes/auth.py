from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.app.core.config import settings
from packages.shared.database.session import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])
password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("business-brain-dummy-password")
ALGORITHM = "HS256"


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=8, max_length=256)
    business_name: str = Field(min_length=2, max_length=255)
    industry: str = Field(min_length=2, max_length=64)


def _normalise(value: str | None) -> str | None:
    value = value.strip() if value else None
    return value.lower() if value else None


def _create_access_token(user_id: UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "user",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def _user_row(db: Session, user_id: UUID):
    return db.execute(
        text("""
            SELECT u.id, u.username, u.email, u.phone, u.is_active,
                   ub.business_id, ub.role, b.name AS business_name, b.industry
            FROM users u
            JOIN user_businesses ub ON ub.user_id = u.id
            JOIN businesses b ON b.id = ub.business_id
            WHERE u.id = :user_id
            ORDER BY ub.created_at
            LIMIT 1
        """),
        {"user_id": str(user_id)},
    ).mappings().first()


def _public_user(row) -> dict:
    return {
        "id": str(row["id"]),
        "username": row["username"],
        "email": row["email"],
        "phone": row["phone"],
        "business": {
            "id": str(row["business_id"]),
            "name": row["business_name"],
            "industry": row["industry"],
            "role": row["role"],
        },
    }


def _find_user(db: Session, identifier: str):
    identifier = identifier.strip()
    normalized = identifier.lower()
    return db.execute(
        text("""
            SELECT id, username, email, phone, password_hash, is_active
            FROM users
            WHERE lower(username) = :identifier
               OR lower(coalesce(email, '')) = :identifier
               OR phone = :raw_identifier
            LIMIT 1
        """),
        {"identifier": normalized, "raw_identifier": identifier},
    ).mappings().first()


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    email = _normalise(payload.email)
    phone = payload.phone.strip() if payload.phone else None

    if not email and not phone:
        raise HTTPException(422, "Provide an email address or phone number")

    existing = db.execute(
        text("""
            SELECT 1 FROM users
            WHERE lower(username) = :username
               OR (:email IS NOT NULL AND lower(email) = :email)
               OR (:phone IS NOT NULL AND phone = :phone)
            LIMIT 1
        """),
        {"username": username.lower(), "email": email, "phone": phone},
    ).first()
    if existing:
        raise HTTPException(409, "An account already exists with that username, email, or phone")

    user_id = uuid4()
    business_id = uuid4()
    try:
        db.execute(
            text("""
                INSERT INTO businesses (id, name, industry)
                VALUES (:id, :name, :industry)
            """),
            {"id": str(business_id), "name": payload.business_name.strip(), "industry": payload.industry.strip().lower()},
        )
        db.execute(
            text("""
                INSERT INTO users (id, username, email, phone, password_hash)
                VALUES (:id, :username, :email, :phone, :password_hash)
            """),
            {
                "id": str(user_id),
                "username": username,
                "email": email,
                "phone": phone,
                "password_hash": password_hash.hash(payload.password),
            },
        )
        db.execute(
            text("""
                INSERT INTO user_businesses (user_id, business_id, role)
                VALUES (:user_id, :business_id, 'owner')
            """),
            {"user_id": str(user_id), "business_id": str(business_id)},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    row = _user_row(db, user_id)
    token = _create_access_token(user_id)
    return {"access_token": token, "token_type": "bearer", "user": _public_user(row)}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = _find_user(db, payload.identifier)
    password_ok = password_hash.verify(payload.password, user["password_hash"] if user else DUMMY_PASSWORD_HASH)
    if not user or not user["is_active"] or not password_ok:
        raise HTTPException(401, "Invalid username, email/phone, or password")

    row = _user_row(db, UUID(str(user["id"])))
    if not row:
        raise HTTPException(403, "Your account is not linked to a business")
    return {
        "access_token": _create_access_token(UUID(str(user["id"]))),
        "token_type": "bearer",
        "user": _public_user(row),
    }


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "User authentication is required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "user" or not payload.get("sub"):
            raise InvalidTokenError("invalid user token")
        user_id = UUID(str(payload["sub"]))
    except (InvalidTokenError, ValueError, TypeError):
        raise HTTPException(401, "Invalid or expired user session")

    row = _user_row(db, user_id)
    if not row or not row["is_active"]:
        raise HTTPException(401, "User session is no longer active")
    return dict(row)


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return _public_user(user)
