from __future__ import annotations

import logging
import time
from pathlib import Path

from apps.connector.business_brain_connector.config import ConnectorConfig
from apps.connector.business_brain_connector.fingerprint import fingerprint
from apps.connector.business_brain_connector.state import SyncState
from apps.connector.business_brain_connector.uploader import UploadError, send_heartbeat, upload_file
from apps.connector.business_brain_connector.watcher import discover_files

logger = logging.getLogger(__name__)


def sync_file(path: str | Path, config: ConnectorConfig, state: SyncState) -> bool:
    """Attempt to sync a single file, with exponential backoff across calls.

    Returns True if the file is now synced (or already was), False if the
    attempt failed and should be retried later. Does not sleep or loop --
    callers control the retry cadence (e.g. the next poll interval).
    """
    path = Path(path)
    checksum = fingerprint(path)

    if state.contains(checksum):
        logger.debug("Skipping already-synced file %s (%s)", path, checksum[:12])
        return True

    if not state.should_retry(checksum, config.max_upload_retries):
        logger.warning(
            "Giving up on %s (%s) after %s failed attempt(s); "
            "fix the underlying issue and delete its entry from the sync-state file to retry.",
            path, checksum[:12], state.attempts(checksum),
        )
        return False

    attempt = state.attempts(checksum)
    if attempt > 0:
        backoff = config.retry_backoff_seconds * (2 ** (attempt - 1))
        logger.info("Retrying %s (attempt %s), backing off %.1fs", path, attempt + 1, backoff)
        time.sleep(backoff)

    try:
        result = upload_file(path, config.business_id, config.api_base_url, config.api_token)
    except UploadError as exc:
        state.mark_failed(checksum, str(path), str(exc))
        logger.error("Upload failed for %s: %s", path, exc)
        return False

    state.mark_synced(checksum, str(path))
    if result.already_imported:
        logger.info("%s was already imported on the server; marked synced.", path)
    else:
        logger.info("Synced %s -> run %s", path, result.response_body.get("run_id", "?"))
    return True


def poll_once(config: ConnectorConfig, state: SyncState) -> bool:
    """Run one discover-and-sync pass over the source folder.

    Returns True if any file needed a sync attempt this pass (new, or a
    previously failed one still within its retry budget), False if every
    discovered file was already synced -- or there was nothing to sync at
    all. The caller uses this to decide whether a heartbeat is needed: a
    successful upload already refreshes the server's last_seen_at, so a
    heartbeat is only useful when nothing else this cycle would have.
    """
    had_activity = False
    for path in discover_files(config.source_dir):
        if not state.contains(fingerprint(path)):
            had_activity = True
        sync_file(path, config, state)
    return had_activity


def send_heartbeat_safely(config: ConnectorConfig) -> None:
    """Best-effort heartbeat -- a failure here should never crash the
    connector's main loop, just get logged so an operator can notice a
    persistent connectivity problem."""
    if not config.api_token:
        return
    try:
        send_heartbeat(config.api_base_url, config.api_token)
        logger.debug("Heartbeat sent")
    except UploadError as exc:
        logger.warning("Heartbeat failed: %s", exc)


def run(config: ConnectorConfig, state_path: str | Path) -> None:
    """Run the connector loop forever: on every poll, re-scan the source
    folder and attempt to sync any file that is not yet successfully synced.
    If nothing needed syncing this cycle, send a heartbeat instead so the
    dashboard's 'last seen' status doesn't go stale just because the source
    folder has been quiet.

    Re-scanning (rather than only reacting to file-change events) is what
    lets a previously-failed upload be retried on a later poll without the
    file itself changing -- dedup and "already handled" are both driven by
    the content fingerprint via SyncState, not by file mtime.
    """
    state = SyncState(state_path)
    logger.info(
        "Connector starting: business=%s source=%s api=%s",
        config.business_id, config.source_dir, config.api_base_url,
    )
    while True:
        had_activity = poll_once(config, state)
        if not had_activity:
            send_heartbeat_safely(config)
        time.sleep(max(1, config.poll_seconds))
