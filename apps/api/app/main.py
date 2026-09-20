from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from apps.api.app.api.routes.health import router as health_router
from apps.api.app.api.routes.auth import router as auth_router
from apps.api.app.api.routes.ingestion import router as ingestion_router
from apps.api.app.api.routes.connectors import router as connectors_router
from apps.api.app.api.routes.kpis import router as kpis_router
from apps.api.app.api.routes.trends import router as trends_router
from apps.api.app.api.routes.dimensions import router as dimensions_router
from apps.api.app.api.routes.signals import router as signals_router
from apps.api.app.api.routes.recommendations import router as recommendations_router
from apps.api.app.api.routes.context import router as context_router
from apps.api.app.api.routes.agent import router as agent_router
from apps.api.app.api.routes.anomalies import router as anomalies_router
from apps.api.app.api.routes.customer_risk import router as customer_risk_router
from apps.api.app.api.routes.customer_concentration import router as customer_concentration_router
from apps.api.app.api.routes.product_risk import router as product_risk_router
from apps.api.app.api.routes.margin import router as margin_router
from apps.api.app.api.routes.receivables import router as receivables_router
from apps.api.app.api.routes.payables import router as payables_router
from apps.api.app.api.routes.supplier_risk import router as supplier_risk_router
from apps.api.app.api.routes.discounts import router as discounts_router
from apps.api.app.api.routes.expenses import router as expenses_router
from apps.api.app.api.routes.inventory import router as inventory_router
from apps.api.app.api.routes.import_history import router as import_history_router
from apps.api.app.api.routes.performance import router as performance_router
from apps.api.app.api.routes.purchases import router as purchases_router
from apps.api.app.api.routes.payments import router as payments_router
from apps.api.app.core.config import settings
from packages.shared.database.session import engine

logger = logging.getLogger(__name__)

docs_enabled = settings.enable_api_docs and not settings.is_production
app = FastAPI(
    title="Business Brain API",
    version="0.1.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

if settings.allowed_host_list and "*" not in settings.allowed_host_list:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Connector-Registration-Key"],
)


@app.middleware("http")
async def production_safety_headers(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.max_upload_bytes:
                return JSONResponse(status_code=413, content={"detail": "Request payload is too large."})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header."})

    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request failure request=%s path=%s", request_id, request.url.path)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error.", "request_id": request_id},
        )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/api/health/ready", tags=["health"])
def readiness():
    """Readiness probe: the process and its primary database must be usable."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check failed")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}


for router in (
    health_router,
    auth_router,
    ingestion_router,
    connectors_router,
    kpis_router,
    trends_router,
    dimensions_router,
    signals_router,
    recommendations_router,
    context_router,
    agent_router,
    anomalies_router,
    customer_risk_router,
    customer_concentration_router,
    product_risk_router,
    margin_router,
    receivables_router,
    payables_router,
    supplier_risk_router,
    discounts_router,
    expenses_router,
    inventory_router,
    import_history_router,
    performance_router,
    purchases_router,
    payments_router,
):
    app.include_router(router, prefix="/api")
