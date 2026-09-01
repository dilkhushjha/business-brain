# Business Brain Connector

Lightweight local connector for a Windows/Tally workstation.

## V2.1 foundation

The connector currently provides the local pieces needed for automatic file synchronization:

- watches a configured folder for CSV/XLS/XLSX files
- fingerprints files with SHA-256
- persists fingerprints locally to avoid reprocessing the same source
- keeps configuration outside the application code
- uses polling only, avoiding extra Windows dependencies

The connector does **not** yet upload files automatically. That is the next milestone: add authenticated upload, retry/backoff, sync audit events and a dashboard sync-status endpoint.
