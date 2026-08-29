from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
app=FastAPI(title="Business Brain API",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
for router in (health_router,ingestion_router,kpis_router,trends_router,dimensions_router,signals_router,recommendations_router,context_router,agent_router,anomalies_router,customer_risk_router,customer_concentration_router,product_risk_router,margin_router,receivables_router,inventory_router): app.include_router(router,prefix="/api")
