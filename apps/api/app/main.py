from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from apps.api.app.api.routes.health import router as health_router
from apps.api.app.api.routes.ingestion import router as ingestion_router
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
from apps.api.app.api.routes.inventory import router as inventory_router
from apps.api.app.api.routes.import_history import router as import_history_router
from packages.shared.database.session import engine


def ensure_schema_compatibility() -> None:
    """Apply additive compatibility changes for databases created by older V1 builds."""
    statements = (
        "ALTER TABLE sales ADD COLUMN IF NOT EXISTS due_date DATE",
        "ALTER TABLE sales ADD COLUMN IF NOT EXISTS paid_amount NUMERIC(18,2) NOT NULL DEFAULT 0",
    )
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


app = FastAPI(title="Business Brain API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep local/dev databases created by previous V1 iterations compatible with
# the current ORM model. These are additive, idempotent changes only.
ensure_schema_compatibility()

for router in (
    health_router,
    ingestion_router,
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
    inventory_router,
    import_history_router,
):
    app.include_router(router, prefix="/api")
