# Business Brain

AI-powered business intelligence and decision support for Indian SMEs.

**V1 — Understand → V2 — Predict → V3 — Act**

Business Brain sits on top of Tally, Excel, CSV and future live integrations to produce evidence-backed metrics, signals, predictions and recommendations.

## Pilot businesses
- Electrical goods wholesaler
- Clothing retailer

## Architecture
A modular monolith with boundaries for domain, data, analytics, ML, intelligence, industry domains and integrations.

## Trust model
FACT → DETECTION → PREDICTION → HYPOTHESIS → RECOMMENDATION.

The LLM is never the authoritative source for numerical business facts.

## Initial stack
Next.js + TypeScript, FastAPI + Python, PostgreSQL + pgvector, Polars/Pandas, Pydantic, RapidFuzz, scikit-learn, Redis/Celery, provider-agnostic LLM adapter, S3/MinIO, Docker and GitHub Actions.

## Roadmap
### V1 — Understand
Ingestion, normalization, canonical model, metrics, signals, evidence-backed insights and conversational Q&A.

### V2 — Predict
Forecasting, anomaly detection, risk models, scenarios, external intelligence and business memory.

### V3 — Act
Live integrations, proactive monitoring, WhatsApp, approval workflows, action execution and outcome tracking.
