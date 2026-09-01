# Business Brain Connector

Lightweight local connector for a Windows/Tally workstation.

## What it does

- watches a configured folder for CSV/XLS/XLSX files
- fingerprints files with SHA-256 so identical content is not re-uploaded
- uploads through the authenticated `/connectors/import/{business_id}` endpoint
- retries failed uploads with exponential backoff
- persists a durable local sync-audit record
- runs as a CLI: `python -m business_brain_connector --config connector.config.json`

## Secure onboarding

1. Start the Business Brain API.
2. In local development, call `POST /api/connectors/register/{business_id}`.
3. In production, configure `CONNECTOR_REGISTRATION_KEY` on the API and send it as
   `X-Connector-Registration-Key` when provisioning a connector.
4. Store the returned connector token in the local connector configuration.

The server stores only a SHA-256 hash of the connector token. The plaintext token
is returned once during registration and is then used as a Bearer credential for
connector heartbeats and uploads.

Example configuration:

```json
{
  "business_id": "...",
  "source_dir": "C:/Tally/Exports",
  "api_base_url": "http://localhost:8000/api",
  "api_token": "...",
  "poll_seconds": 30,
  "max_upload_retries": 5,
  "retry_backoff_seconds": 5.0
}
```

## API capabilities

- `POST /api/connectors/register/{business_id}` — provision a connector credential
- `POST /api/connectors/heartbeat` — authenticated connectivity check
- `POST /api/connectors/import/{business_id}` — authenticated source import
- `GET /api/connectors/status/{business_id}` — dashboard-facing connector status

The current status endpoint exposes connection metadata, last sync timestamps and
last error; the next UI milestone can surface this as a compact Data Connection card.
