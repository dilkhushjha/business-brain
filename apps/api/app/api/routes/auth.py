from __future__ import annotations

import hashlib
import json
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response
from jwt import InvalidTokenError
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

REFRESH_COOKIE = "bb_refresh_token"
RATE_LIMIT_WINDOW = timedelta(minutes=15)
MAX_LOGIN_FAILURES = 5


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


class PasswordResetRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(min_length=8, max_length=256)


def _normalise(value: str | None) -> str | None:
    value = value.strip() if value else None
    return value.lower() if value else None


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _as_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _create_access_token(user_id: UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "user",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        httponly=True,
        secure=settings.is_production,
        samesite="none" if settings.is_production else "lax",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")


def _issue_refresh_token(db: Session, user_id: UUID) -> str:
    raw = secrets.token_urlsafe(48)
    db.execute(
        text("""
            INSERT INTO auth_refresh_tokens (id, user_id, token_hash, expires_at)
            VALUES (:id, :user_id, :token_hash, :expires_at)
        """),
        {
            "id": uuid4().hex,
            "user_id": user_id.hex,
            "token_hash": _token_hash(raw),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        },
    )
    return raw


def _rotate_refresh_token(db: Session, raw_token: str) -> tuple[UUID, str] | None:
    row = db.execute(
        text("""
            SELECT id, user_id, expires_at, revoked_at
            FROM auth_refresh_tokens
            WHERE token_hash=:token_hash
            LIMIT 1
        """),
        {"token_hash": _token_hash(raw_token)},
    ).mappings().first()
    now = datetime.now(timezone.utc)
    if not row or row["revoked_at"] is not None or _as_datetime(row["expires_at"]) <= now:
        return None

    new_id = uuid4()
    new_raw = secrets.token_urlsafe(48)
    db.execute(
        text("""
            INSERT INTO auth_refresh_tokens (id, user_id, token_hash, expires_at)
            VALUES (:id, :user_id, :token_hash, :expires_at)
        """),
        {
            "id": new_id.hex,
            "user_id": str(row["user_id"]),
            "token_hash": _token_hash(new_raw),
            "expires_at": now + timedelta(days=settings.refresh_token_expire_days),
        },
    )
    db.execute(
        text("""
            UPDATE auth_refresh_tokens
            SET revoked_at=:revoked_at, replaced_by_id=:replaced_by_id
            WHERE id=:id
        """),
        {"revoked_at": now, "replaced_by_id": new_id.hex, "id": str(row["id"])},
    )
    return UUID(str(row["user_id"])), new_raw


def _user_row(db: Session, user_id: UUID):
    return db.execute(
        text("""
            SELECT u.id, u.username, u.email, u.phone, u.is_active,
                   ub.business_id, ub.role, b.name AS business_name, b.industry,
                   b.currency_code, b.timezone, b.fiscal_year_start_month,
                   b.onboarding_completed, b.onboarding_completed_at
            FROM users u
            JOIN user_businesses ub ON ub.user_id = u.id
            JOIN businesses b ON b.id = ub.business_id
            WHERE u.id = :user_id
            ORDER BY ub.created_at
            LIMIT 1
        """),
        {"user_id": user_id.hex},
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
            "currency_code": row["currency_code"],
            "timezone": row["timezone"],
            "fiscal_year_start_month": int(row["fiscal_year_start_month"]),
            "onboarding_completed": bool(row["onboarding_completed"]),
            "onboarding_completed_at": row["onboarding_completed_at"].isoformat() if row["onboarding_completed_at"] else None,
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


def _rate_key(request: Request, identifier: str) -> str:
    host = request.client.host if request.client else "unknown"
    raw = f"{host}:{identifier.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _login_failure_count(db: Session, key: str) -> int:
    now = datetime.now(timezone.utc)
    row = db.execute(
        text("""
            INSERT INTO auth_rate_limits (key, window_started_at, failed_attempts)
            VALUES (:key, :now, 1)
            ON CONFLICT (key) DO UPDATE
            SET failed_attempts = CASE
                    WHEN auth_rate_limits.window_started_at <= :cutoff THEN 1
                    ELSE auth_rate_limits.failed_attempts + 1
                END,
                window_started_at = CASE
                    WHEN auth_rate_limits.window_started_at <= :cutoff THEN :now
                    ELSE auth_rate_limits.window_started_at
                END
            RETURNING failed_attempts
        """),
        {"key": key, "now": now, "cutoff": now - RATE_LIMIT_WINDOW},
    ).first()
    return int(row[0]) if row else MAX_LOGIN_FAILURES


def _clear_login_failures(db: Session, key: str) -> None:
    db.execute(text("DELETE FROM auth_rate_limits WHERE key=:key"), {"key": key})


def _security_event(
    db: Session,
    request: Request,
    event_type: str,
    success: bool,
    user_id: UUID | None = None,
    business_id: UUID | None = None,
    metadata: dict | None = None,
) -> None:
    db.execute(
        text("""
            INSERT INTO security_events
              (id, user_id, business_id, event_type, success, ip_address, user_agent, metadata)
            VALUES (:id, :user_id, :business_id, :event_type, :success, :ip_address, :user_agent, :metadata)
        """),
        {
            "id": uuid4().hex,
            "user_id": user_id.hex if user_id else None,
            "business_id": business_id.hex if business_id else None,
            "event_type": event_type,
            "success": success,
            "ip_address": request.client.host if request.client else None,
            "user_agent": (request.headers.get("user-agent") or "")[:512] or None,
            "metadata": json.dumps(metadata or {}, separators=(",", ":")),
        },
    )


def _send_password_reset_email(email: str, token: str) -> None:
    if not settings.smtp_host or not settings.smtp_from:
        if not settings.is_production:
            return
        raise RuntimeError("Password reset email delivery is not configured")

    message = EmailMessage()
    message["Subject"] = "Reset your Business Brain password"
    message["From"] = settings.smtp_from
    message["To"] = email
    message.set_content(
        "We received a request to reset your Business Brain password.\n\n"
        f"Reset your password here: {settings.password_reset_url}?token={token}\n\n"
        "This link expires soon and can only be used once. If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


def _login_response(db: Session, response: Response, user_id: UUID, request: Request):
    refresh = _issue_refresh_token(db, user_id)
    row = _user_row(db, user_id)
    _security_event(db, request, "login_success", True, user_id=user_id, business_id=UUID(str(row["business_id"])))
    db.commit()
    _set_refresh_cookie(response, refresh)
    return {"access_token": _create_access_token(user_id), "token_type": "bearer", "user": _public_user(row)}


@router.post("/register")
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
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
                INSERT INTO businesses (id, name, industry, created_at)
                VALUES (:id, :name, :industry, :created_at)
            """),
            {
                "id": business_id.hex,
                "name": payload.business_name.strip(),
                "industry": payload.industry.strip().lower(),
                "created_at": datetime.utcnow(),
            },
        )
        db.execute(
            text("""
                INSERT INTO users (id, username, email, phone, password_hash)
                VALUES (:id, :username, :email, :phone, :password_hash)
            """),
            {
                "id": user_id.hex,
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
            {"user_id": user_id.hex, "business_id": business_id.hex},
        )
        _security_event(db, request, "account_registered", True, user_id=user_id, business_id=business_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    row = _user_row(db, user_id)
    token = _issue_refresh_token(db, user_id)
    db.commit()
    _set_refresh_cookie(response, token)
    return {"access_token": _create_access_token(user_id), "token_type": "bearer", "user": _public_user(row)}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    key = _rate_key(request, payload.identifier)
    failure_count = db.execute(
        text("""
            SELECT failed_attempts, window_started_at
            FROM auth_rate_limits WHERE key=:key
        """),
        {"key": key},
    ).mappings().first()
    now = datetime.now(timezone.utc)
    if failure_count and _as_datetime(failure_count["window_started_at"]) > now - RATE_LIMIT_WINDOW and int(failure_count["failed_attempts"]) >= MAX_LOGIN_FAILURES:
        retry_after = max(1, int((_as_datetime(failure_count["window_started_at"]) + RATE_LIMIT_WINDOW - now).total_seconds()))
        raise HTTPException(429, "Too many failed login attempts. Try again later.", headers={"Retry-After": str(retry_after)})

    user = _find_user(db, payload.identifier)
    password_ok = password_hash.verify(payload.password, user["password_hash"] if user else DUMMY_PASSWORD_HASH)
    if not user or not user["is_active"] or not password_ok:
        attempts = _login_failure_count(db, key)
        _security_event(db, request, "login_failure", False, metadata={"attempts": attempts})
        db.commit()
        raise HTTPException(401, "Invalid username, email/phone, or password")

    _clear_login_failures(db, key)
    return _login_response(db, response, UUID(str(user["id"])), request)


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db), refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE)):
    if not refresh_token:
        raise HTTPException(401, "Invalid or expired user session")
    rotated = _rotate_refresh_token(db, refresh_token)
    if not rotated:
        db.rollback()
        raise HTTPException(401, "Invalid or expired user session")
    user_id, new_refresh = rotated
    row = _user_row(db, user_id)
    if not row or not row["is_active"]:
        db.rollback()
        _clear_refresh_cookie(response)
        raise HTTPException(401, "User session is no longer active")
    _security_event(db, request, "token_refresh", True, user_id=user_id, business_id=UUID(str(row["business_id"])))
    db.commit()
    _set_refresh_cookie(response, new_refresh)
    return {"access_token": _create_access_token(user_id), "token_type": "bearer", "user": _public_user(row)}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    if refresh_token:
        db.execute(
            text("UPDATE auth_refresh_tokens SET revoked_at=:now WHERE token_hash=:token_hash AND revoked_at IS NULL"),
            {"now": datetime.now(timezone.utc), "token_hash": _token_hash(refresh_token)},
        )
        _security_event(db, request, "logout", True)
        db.commit()
    _clear_refresh_cookie(response)
    return {"status": "signed_out"}


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


@router.post("/password-reset/request", status_code=202)
def request_password_reset(payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    user = _find_user(db, payload.identifier)
    if not user or not user["is_active"] or not user["email"]:
        _security_event(db, request, "password_reset_request", True, metadata={"matched": False})
        db.commit()
        return {"detail": "If an account matches, a reset link will be sent."}

    raw = secrets.token_urlsafe(48)
    db.execute(
        text("UPDATE password_reset_tokens SET used_at=:now WHERE user_id=:user_id AND used_at IS NULL"),
        {"now": datetime.now(timezone.utc), "user_id": str(user["id"])},
    )
    db.execute(
        text("""
            INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at)
            VALUES (:id, :user_id, :token_hash, :expires_at)
        """),
        {
            "id": uuid4().hex,
            "user_id": str(user["id"]),
            "token_hash": _token_hash(raw),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_expire_minutes),
        },
    )
    try:
        _send_password_reset_email(user["email"], raw)
    except Exception:
        db.rollback()
        raise HTTPException(503, "Password reset delivery is temporarily unavailable")
    _security_event(db, request, "password_reset_request", True, user_id=UUID(str(user["id"])), metadata={"delivery": "sent"})
    db.commit()
    return {"detail": "If an account matches, a reset link will be sent."}


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, request: Request, response: Response, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT id, user_id, expires_at, used_at
            FROM password_reset_tokens
            WHERE token_hash=:token_hash
            LIMIT 1
        """),
        {"token_hash": _token_hash(payload.token)},
    ).mappings().first()
    now = datetime.now(timezone.utc)
    if not row or row["used_at"] is not None or _as_datetime(row["expires_at"]) <= now:
        _security_event(db, request, "password_reset_confirm", False)
        db.commit()
        raise HTTPException(400, "Invalid or expired password reset link")

    user_id = UUID(str(row["user_id"]))
    db.execute(
        text("UPDATE users SET password_hash=:password_hash WHERE id=:user_id"),
        {"password_hash": password_hash.hash(payload.password), "user_id": user_id.hex},
    )
    db.execute(
        text("UPDATE password_reset_tokens SET used_at=:now WHERE id=:id"),
        {"now": now, "id": str(row["id"])},
    )
    db.execute(
        text("UPDATE auth_refresh_tokens SET revoked_at=:now WHERE user_id=:user_id AND revoked_at IS NULL"),
        {"now": now, "user_id": user_id.hex},
    )
    _security_event(db, request, "password_reset_confirm", True, user_id=user_id)
    db.commit()
    _clear_refresh_cookie(response)
    return {"detail": "Password updated. Please sign in again."}
