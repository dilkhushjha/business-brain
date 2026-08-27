from pathlib import Path
import polars as pl
from .base import DataSourceAdapter
class ExcelAdapter(DataSourceAdapter):
    def inspect(self, path: Path) -> dict:
        f = pl.read_excel(path); return {"rows": f.height, "columns": f.columns}
    def ingest(self, path: Path) -> list[dict]: return pl.read_excel(path).to_dicts()
