from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class SyncState:
    """Durable local sync-audit store for connector fingerprints.

    Each fingerprint maps to a small record tracking whether it has been
    successfully synced, how many upload attempts have been made, and the
    last error (if any) -- this is what drives retry/backoff and gives an
    operator something to inspect if a file is stuck.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.values: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.values = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self.values = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.values, indent=2), encoding="utf-8")

    def contains(self, checksum: str) -> bool:
        """True only for fingerprints that have successfully synced -- a
        fingerprint that previously failed remains eligible for retry."""
        record = self.values.get(checksum)
        return bool(record) and record.get("status") == "synced"

    def attempts(self, checksum: str) -> int:
        return self.values.get(checksum, {}).get("attempts", 0)

    def should_retry(self, checksum: str, max_attempts: int) -> bool:
        record = self.values.get(checksum)
        if record is None:
            return True
        return record.get("status") != "synced" and record.get("attempts", 0) < max_attempts

    def mark_synced(self, checksum: str, source: str) -> None:
        record = self.values.setdefault(checksum, {"attempts": 0})
        record.update(
            {
                "source": source,
                "status": "synced",
                "attempts": record.get("attempts", 0) + 1,
                "last_attempt": _now_iso(),
                "last_error": None,
            }
        )
        self._save()

    def mark_failed(self, checksum: str, source: str, error: str) -> None:
        record = self.values.setdefault(checksum, {"attempts": 0})
        record.update(
            {
                "source": source,
                "status": "failed",
                "attempts": record.get("attempts", 0) + 1,
                "last_attempt": _now_iso(),
                "last_error": error,
            }
        )
        self._save()

    def pending(self) -> dict[str, dict[str, Any]]:
        """Fingerprints that have not (yet) synced successfully -- useful for
        a future sync-status view."""
        return {checksum: record for checksum, record in self.values.items() if record.get("status") != "synced"}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
