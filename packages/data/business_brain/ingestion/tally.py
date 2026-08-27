from pathlib import Path
from .base import DataSourceAdapter
class TallyExportAdapter(DataSourceAdapter):
    """Boundary for Tally exports; exact mapping is finalized per pilot format."""
    def inspect(self, path: Path) -> dict: return {"path": str(path), "status": "adapter-ready"}
    def ingest(self, path: Path) -> list[dict]: raise NotImplementedError
