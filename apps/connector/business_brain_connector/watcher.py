from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterator

SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xls"}


def discover_files(source_dir: str | Path) -> list[Path]:
    """Return supported source files in deterministic order."""
    root = Path(source_dir).expanduser()
    if not root.exists():
        return []
    return sorted(
        (path for path in root.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES),
        key=lambda path: path.stat().st_mtime_ns,
    )


def watch(source_dir: str | Path, poll_seconds: int = 30) -> Iterator[Path]:
    """Yield a file once when its path/mtime/size changes.

    This polling watcher intentionally has no third-party dependency so the
    connector can run on a typical Windows Tally machine with minimal setup.
    """
    seen: dict[str, tuple[int, int]] = {}
    while True:
        for path in discover_files(source_dir):
            stat = path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            key = str(path.resolve()).lower()
            if seen.get(key) != signature:
                seen[key] = signature
                yield path
        time.sleep(max(1, poll_seconds))


def run(source_dir: str | Path, on_file: Callable[[Path], None], poll_seconds: int = 30) -> None:
    for path in watch(source_dir, poll_seconds):
        on_file(path)
