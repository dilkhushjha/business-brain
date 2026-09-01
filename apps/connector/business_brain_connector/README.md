# Business Brain Connector

Lightweight local connector for a Windows/Tally workstation.

## What it does

- watches a configured folder for CSV/XLS/XLSX files (`watcher.py`)
- fingerprints files with SHA-256 so re-processing the same content is a no-op (`fingerprint.py`)
- uploads new/changed files to the ingestion API's `/ingestion/import/{business_id}` endpoint,
  with an optional bearer token, using only the standard library so no extra
  dependency is required on the Tally machine (`uploader.py`)
- retries a failed upload with exponential backoff, up to a configurable
  attempt budget, and gives up (logging why) once that budget is exhausted (`sync.py`)
- persists a durable local sync-audit record per file: status, attempt
  count, last-attempt time and last error, so an operator can see why a
  file is stuck (`state.py`)
- runs as a CLI: `python -m business_brain_connector --config connector.config.json`

## Configuration

A JSON file (see `ConnectorConfig` in `config.py`):

```json
{
  "business_id": "...",
  "source_dir": "C:/Tally/Exports",
  "api_base_url": "https://api.example.com/api",
  "api_token": "...",
  "poll_seconds": 30,
  "max_upload_retries": 5,
  "retry_backoff_seconds": 5.0
}
```

## Not yet built

- A dashboard-facing sync-status endpoint on the API, so the web app can
  show connector health/last-sync-time for a business, rather than the
  audit trail only existing locally on the Tally machine.
- The backend ingestion endpoint itself does not yet enforce the bearer
  token the connector already sends -- API-side auth is a separate,
  larger piece of work.

