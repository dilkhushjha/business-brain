# Security

- Tenant isolation on business records.
- Secrets only through environment/secret management.
- Minimize raw business data sent to LLMs.
- Audit imports and future actions.
- Preserve provenance for insights.
- Human approval for consequential actions.

## Implementation status

**Every `{business_id}`-scoped API route now requires a Bearer token**
(`require_business_access` in `apps/api/app/api/connector_auth.py`), checked
against that specific business_id -- a token issued for one business gets a
403 on another business's data. Verified with real HTTP-level tests
(`tests/integration/test_api_auth.py`), not just the auth function in
isolation.

V1 has no separate user/login system. The one credential a business has --
the token issued by `POST /connectors/register/{business_id}` -- doubles as
both the automated connector's upload credential and the general API access
token for that business's dashboard/chat. This is a deliberate simplification
for the pilot stage, not an oversight; splitting these into distinct
credential types is future work once there's a real login system.

**Immediate consequence, not yet addressed**: `apps/web` sends no
`Authorization` header at all today. Locking down the API means the existing
dashboard/chat UI will get 401s on every request until the frontend is
updated to obtain and send a token -- that update hasn't been made yet.

**Still open:**
- `GET /health` remains intentionally unauthenticated (infra/load-balancer
  checks, no business data).
- No rate limiting on any route.
- No token rotation/revocation flow beyond a connector's `status` being
  set inactive directly in the database.
- The connector-token table (`business_brain_connectors`) is created via
  raw SQL in two separate places (`connector_auth.py` and `main.py`)
  rather than through the Alembic migrations the rest of the schema uses.

