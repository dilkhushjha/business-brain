# Business Brain Connector

Lightweight local connector for a Windows/Tally workstation.

## What it does

- watches a configured folder for CSV/XLS/XLSX files
- fingerprints files with SHA-256 so identical content is not re-uploaded
- uploads through the authenticated `/connectors/import/{business_id}` endpoint
- retries failed uploads with exponential backoff
- sends a heartbeat when a poll cycle finds nothing new to sync, so a
  connector pointed at a quiet folder doesn't look stale on the dashboard
  (a successful upload already refreshes the server's `last_seen_at` on its
  own, so this only fires when nothing else this cycle would have)
- persists a durable local sync-audit record
- runs as a CLI

## Getting started

```
python -m business_brain_connector register \
  --business-id <uuid> \
  --source-dir "C:/Tally/Exports" \
  --api-base-url http://localhost:8000/api \
  --registration-key <key, if the server requires one>
```

This exchanges the registration key for a connector token and writes a
ready-to-use `connector.config.json`. From then on, everything runs
unattended:

```
python -m business_brain_connector run --config connector.config.json
```

(Invoking with no subcommand -- `python -m business_brain_connector --config
connector.config.json` -- still works and is treated as `run`, for anyone
following an older command from before `register` existed.)

## Secure onboarding (what `register` does under the hood)

1. Start the Business Brain API.
2. In local development, `register` calls `POST /api/connectors/register/{business_id}`
   with no key required.
3. In production, configure `CONNECTOR_REGISTRATION_KEY` on the API and pass
   `--registration-key` (sent as `X-Connector-Registration-Key`) when provisioning
   a connector.
4. The returned connector token is written into the local connector configuration
   automatically.

The server stores only a SHA-256 hash of the connector token. The plaintext token
is returned once during registration and is then used as a Bearer credential for
connector heartbeats and uploads.

Example configuration (written by `register`, or hand-edited):

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

## Known limitation

Re-uploading a source file that contains an invoice already stored in the
database does not update that invoice (see `persist_sales()` in the
ingestion pipeline) -- it's skipped entirely, including any changed
due-date/payment-status columns. Reconciling updates to already-ingested
invoices is a distinct, larger piece of work from what this connector does
today (pure new-file sync), not something the connector itself can paper
over.

