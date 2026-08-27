from fastapi import FastAPI

from apps.api.app.api.routes.health import router as health_router
from apps.api.app.api.routes.ingestion import router as ingestion_router
from apps.api.app.api.routes.kpis import router as kpis_router
from apps.api.app.api.routes.dimensions import router as dimensions_router
from apps.api.app.api.routes.signals import router as signals_router
from apps.api.app.api.routes.recommendations import router as recommendations_router
from apps.api.app.api.routes.context import router as context_router
from apps.api.app.api.routes.agent import router as agent_router

app = FastAPI(title="Business Brain API", version="0.1.0")
app.include_router(health_router, prefix="/api")
app.include_router(ingestion_router, prefix="/api")
app.include_router(kpis_router, prefix="/api")
app.include_router(dimensions_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(context_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
