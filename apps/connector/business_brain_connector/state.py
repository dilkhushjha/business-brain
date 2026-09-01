from __future__ import annotations

import json
from pathlib import Path


class SyncState:
    """Small durable local state store for connector fingerprints."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.values: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.values = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self.values = {}

    def contains(self, checksum: str) -> bool:
        return checksum in self.values

    def mark_synced(self, checksum: str, source: str) -> None:
        self.values[checksum] = {"source": source}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.values, indent=2), encoding="utf-8")
