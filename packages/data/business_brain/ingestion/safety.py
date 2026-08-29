from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ImportDecision:
    allowed: bool
    reason: str
    rows_to_import: int
    preserves_existing_data: bool = True

def decide_import(rows_read:int, rows_accepted:int, rows_rejected:int, allow_partial:bool=False)->ImportDecision:
    if rows_read == 0:
        return ImportDecision(False,"The file contains no data rows.",0)
    if rows_rejected and not allow_partial:
        return ImportDecision(False,f"Validation failed for {rows_rejected} row(s). Fix the file and preview again.",0)
    if rows_accepted == 0:
        return ImportDecision(False,"No valid rows are available for import.",0)
    return ImportDecision(True,"Import is safe to commit.",rows_accepted)
