from __future__ import annotations

import hashlib
from pathlib import Path


def fingerprint(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a stable SHA-256 fingerprint for a source file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
