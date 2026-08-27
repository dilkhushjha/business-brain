from fastapi import FastAPI

from apps.api.app.api.routes.health import router as health_router

app = FastAPI(title="Business Brain API", version="0.1.0")
app.include_router(health_router, prefix="/api")
