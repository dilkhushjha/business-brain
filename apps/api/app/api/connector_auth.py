from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from packages.shared.database.session import get_db


def ensure_connector_schema(db: Session) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS business_brain_connectors (
            id UUID PRIMARY KEY,
            business_id UUID NOT NULL,
            name VARCHAR(255) NOT NULL DEFAULT 'Business Brain Connector',
            token_hash VARCHAR(64) NOT NULL UNIQUE,
            token_prefix VARCHAR(16) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            version VARCHAR(32),
            last_seen_at TIMESTAMPTZ,
            last_sync_at TIMESTAMPTZ,
            last_success_at TIMESTAMPTZ,
            last_error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_connector(db: Session, business_id: UUID, name: str = "Business Brain Connector") -> tuple[UUID, str]:
    ensure_connector_schema(db)
    connector_id = UUID(bytes=secrets.token_bytes(16))
    token = secrets.token_urlsafe(32)
    db.execute(
        text("""
            INSERT INTO business_brain_connectors
                (id, business_id, name, token_hash, token_prefix, status)
            VALUES (:id, :business_id, :name, :token_hash, :token_prefix, 'active')
        """),
        {
            "id": connector_id,
            "business_id": business_id,
            "name": name,
            "token_hash": hash_token(token),
            "token_prefix": token[:12],
        },
    )
    db.commit()
    return connector_id, token


def authenticate_connector(
    db: Session,
    token: str,
    business_id: UUID | None = None,
) -> dict:
    ensure_connector_schema(db)
    row = db.execute(
        text("""
            SELECT id, business_id, status
            FROM business_brain_connectors
            WHERE token_hash = :token_hash
        """),
        {"token_hash": hash_token(token)},
    ).mappings().first()
    if not row or row["status"] != "active":
        raise HTTPException(401, "Invalid or inactive connector credential")
    if business_id is not None and row["business_id"] != business_id:
        raise HTTPException(403, "Connector is not authorized for this business")

    db.execute(
        text("""
            UPDATE business_brain_connectors
            SET last_seen_at = :now, last_error = NULL
            WHERE id = :id
        """),
        {"now": datetime.now(timezone.utc), "id": row["id"]},
    )
    db.commit()
    return dict(row)


def require_connector(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Connector bearer token is required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Connector bearer token is required")
    return authenticate_connector(db, token)


def mark_connector_sync(db: Session, connector_id: UUID, success: bool, error: str | None = None) -> None:
    column = "last_success_at" if success else "last_error"
    if success:
        db.execute(
            text("""
                UPDATE business_brain_connectors
                SET last_sync_at=:now, last_success_at=:now, status='active', last_error=NULL
                WHERE id=:id
            """),
            {"now": datetime.now(timezone.utc), "id": connector_id},
        )
    else:
        db.execute(
            text("""
                UPDATE business_brain_connectors
                SET last_sync_at=:now, last_error=:error
                WHERE id=:id
            """),
            {"now": datetime.now(timezone.utc), "id": connector_id, "error": error},
        )
    db.commit()
