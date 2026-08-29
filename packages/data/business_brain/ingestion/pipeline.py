from pathlib import Path
from .csv import CSVAdapter
from .excel import ExcelAdapter
from .fingerprint import sha256_file
from .models import IngestionIssue, IngestionResult, SourceFile

class IngestionPipeline:
    """V1 ingestion boundary with source adapter selection and metadata."""
    def _adapter(self,path:Path):
        suffix=path.suffix.lower()
        if suffix==".csv": return CSVAdapter()
        if suffix in {".xlsx",".xls"}: return ExcelAdapter()
        raise ValueError(f"Unsupported source format: {suffix}")
    def run(self,path:Path)->IngestionResult:
        adapter=self._adapter(path)
        source=SourceFile(name=path.name,checksum=sha256_file(path),size_bytes=path.stat().st_size,imported_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))
        rows=adapter.ingest(path); issues:list[IngestionIssue]=[]
        return IngestionResult(source=source,rows_read=len(rows),rows_accepted=len(rows),rows_rejected=0,issues=issues)
