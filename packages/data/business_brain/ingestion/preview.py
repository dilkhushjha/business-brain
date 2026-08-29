from pathlib import Path
from typing import Any
from .column_mapping import suggest_mapping
from .pipeline import IngestionPipeline

def preview(path: str | Path) -> dict[str, Any]:
    p=Path(path); result=IngestionPipeline().run(p)
    adapter=IngestionPipeline()._adapter(p); rows=adapter.ingest(p)
    columns=list(rows[0].keys()) if rows else []
    return {"source":result.source.name,"checksum":result.source.checksum,"columns":columns,"mapping":[m.__dict__ for m in suggest_mapping(columns)],"rows_read":result.rows_read,"rows_accepted":result.rows_accepted,"rows_rejected":result.rows_rejected}
