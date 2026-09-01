from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.app.api.connector_auth import create_connector, require_connector
from packages.shared.database.session import get_db

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.post("/register/{business_id}")
def register_connector(business_id: UUID, db: Session = Depends(get_db)):
    connector_id, token = create_connector(db, business_id)
    return {
        "connector_id": str(connector_id),
        "business_id": str(business_id),
        "token": token,
        "warning": "Store this token securely. It is shown only once.",
    }


@router.post("/heartbeat")
def heartbeat(connector: dict = Depends(require_connector)):
    return {
        "status": "connected",
        "connector_id": str(connector["id"]),
        "business_id": str(connector["business_id"]),
    }


@router.get("/status/{business_id}")
def connector_status(
    business_id: UUID,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("""
            SELECT id, name, status, version, last_seen_at, last_sync_at,
                   last_success_at, last_error, created_at
            FROM business_brain_connectors
            WHERE business_id=:business_id
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"business_id": business_id},
    ).mappings().first()
    if not row:
        return {"status": "not_configured", "business_id": str(business_id)}
    return {
        "status": row["status"],
        "connector_id": str(row["id"]),
        "name": row["name"],
        "version": row["version"],
        "last_seen_at": row["last_seen_at"],
        "last_sync_at": row["last_sync_at"],
        "last_success_at": row["last_success_at"],
        "last_error": row["last_error"],
        "created_at": row["created_at"],
    }
