from fastapi import FastAPI

from apps.api.app.api.routes.health import router as health_router
from apps.api.app.api.routes.ingestion import router as ingestion_router
from apps.api.app.api.routes.kpis import router as kpis_router
from apps.api.app.api.routes.dimensions import router as dimensions_router

app = FastAPI(title="Business Brain API", version="0.1.0")
app.include_router(health_router, prefix="/api")
app.include_router(ingestion_router, prefix="/api")
app.include_router(kpis_router, prefix="/api")
app.include_router(dimensions_router, prefix="/api")
