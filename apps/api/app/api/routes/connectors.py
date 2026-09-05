from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.api.connector_auth import create_connector, mark_connector_sync, require_business_access, require_connector
from apps.api.app.api.routes.ingestion import _prepare_upload
from packages.data.business_brain.ingestion.persistence import persist_ingestion_run
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.session import get_db

router = APIRouter(prefix="/connectors", tags=["connectors"])
logger = logging.getLogger(__name__)


@router.post("/register/{business_id}")
def register_connector(
    business_id: UUID,
    db: Session = Depends(get_db),
    registration_key: str | None = Header(default=None, alias="X-Connector-Registration-Key"),
):
    from apps.api.app.core.config import settings
    import hmac

    expected = settings.connector_registration_key
    if expected:
        if not registration_key or not hmac.compare_digest(registration_key, expected):
            raise HTTPException(401, "A valid connector registration key is required")
    elif settings.app_env.lower() not in {"development", "dev", "local"}:
        raise HTTPException(503, "Connector registration is not configured")

    connector_id, token = create_connector(db, business_id)
    warning = "Store this token securely. It is shown only once."
    if not expected:
        warning += " Development registration is open; configure CONNECTOR_REGISTRATION_KEY before production use."
    return {"connector_id": str(connector_id), "business_id": str(business_id), "token": token, "warning": warning}


@router.post("/heartbeat")
def heartbeat(connector: dict = Depends(require_connector)):
    return {"status": "connected", "connector_id": str(connector["id"]), "business_id": str(connector["business_id"])}


@router.post("/import/{business_id}")
def connector_import(
    business_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    connector: dict = Depends(require_connector),
):
    if UUID(str(connector["business_id"])) != business_id:
        raise HTTPException(403, "Connector is not authorized for this business")

    request_id = str(uuid4())
    temp_path: str | None = None
    try:
        result, prepared, temp_path = _prepare_upload(file, business_id, db)
        if result.rows_rejected:
            raise HTTPException(422, detail=f"Import blocked: {result.rows_rejected} row(s) failed validation")
        run = persist_ingestion_run(db, business_id, result)
        created_sales = persist_sales(db, business_id, [row.values for row in prepared])
        db.commit()
        db.refresh(run)
        mark_connector_sync(db, UUID(str(connector["id"])), True)
        return {
            "run_id": str(run.id), "status": run.status, "source": result.source.name,
            "checksum": result.source.checksum, "rows_read": result.rows_read,
            "rows_accepted": result.rows_accepted, "rows_rejected": result.rows_rejected,
            "sales_created": created_sales, "request_id": request_id,
            "connector_id": str(connector["id"]),
        }
    except HTTPException as exc:
        db.rollback()
        mark_connector_sync(db, UUID(str(connector["id"])), False, str(exc.detail))
        raise
    except IntegrityError as exc:
        db.rollback()
        error = "Source or business record already exists"
        mark_connector_sync(db, UUID(str(connector["id"])), False, error)
        raise HTTPException(409, f"{error}. Request: {request_id}") from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Connector ingestion failure request=%s connector=%s", request_id, connector["id"])
        error = f"{type(exc).__name__}: {str(exc).strip()}"
        mark_connector_sync(db, UUID(str(connector["id"])), False, error)
        raise HTTPException(500, f"Import failed; no partial data was committed. {error} Request: {request_id}") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@router.get("/status/{business_id}")
def connector_status(business_id: UUID, db: Session = Depends(get_db), _auth: dict = Depends(require_business_access)):
    row = db.execute(
        text("""
            SELECT id, name, status, version, last_seen_at, last_sync_at,
                   last_success_at, last_error, created_at
            FROM business_brain_connectors
            WHERE business_id=:business_id ORDER BY created_at DESC LIMIT 1
        """), {"business_id": str(business_id)}
    ).mappings().first()
    if not row:
        return {"status": "not_configured", "business_id": str(business_id)}
    return {
        "status": row["status"], "connector_id": str(row["id"]), "name": row["name"],
        "version": row["version"], "last_seen_at": row["last_seen_at"],
        "last_sync_at": row["last_sync_at"], "last_success_at": row["last_success_at"],
        "last_error": row["last_error"], "created_at": row["created_at"],
    }
