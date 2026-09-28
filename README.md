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


## Hourly synthetic demo (development only)

The repository includes `scripts/hourly_demo.py`, which generates related sales and
purchase CSV files and imports them through the same CSV preparation, canonicalization,
and persistence functions used by the API. Each batch uses unique invoice numbers,
purchases each product before recording its sales, and writes the source CSVs to
`data/hourly_demo/` by default.

Apply database migrations first:

```powershell
alembic upgrade head
```

Run one batch to verify the setup:

```powershell
$env:BB_DEMO_BUSINESS_ID = "<your-business-uuid>"
python -m scripts.hourly_demo --once
```

Run continuously, importing immediately and then once every hour:

```powershell
python -m scripts.hourly_demo
```

To test a faster cycle, use (for example) `--interval-seconds 300`. Use
`--no-immediate-run` to wait for the first interval. The process must remain running
for recurring imports; stop it with Ctrl+C. Alternatively, run the `--once` command
from Windows Task Scheduler on an hourly trigger.

**Important:** this is synthetic demo data, not a production integration. It writes
directly to the database configured by `DATABASE_URL` and creates real sales,
purchases, inventory movements, source-file records, and ingestion runs. Use a
dedicated demo business/database, never a live business. Generated records are not
automatically deleted.
