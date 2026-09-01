from __future__ import annotations

import logging
import time
from pathlib import Path

from apps.connector.business_brain_connector.config import ConnectorConfig
from apps.connector.business_brain_connector.fingerprint import fingerprint
from apps.connector.business_brain_connector.state import SyncState
from apps.connector.business_brain_connector.uploader import UploadError, upload_file
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


def run(config: ConnectorConfig, state_path: str | Path) -> None:
    """Run the connector loop forever: on every poll, re-scan the source
    folder and attempt to sync any file that is not yet successfully synced.

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
        for path in discover_files(config.source_dir):
            sync_file(path, config, state)
        time.sleep(max(1, config.poll_seconds))
