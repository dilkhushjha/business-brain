from __future__ import annotations
from typing import Any

def evidence_summary(evidence:list[dict[str,Any]])->list[str]:
    out=[]
    for item in evidence[:6]:
        metric=item.get("metric") or item.get("name")
        value=item.get("value")
        if metric is not None and value is not None: out.append(f"{metric}: {value}")
    return out

def confidence_label(confidence:float|None)->str:
    if confidence is None:return "unknown"
    if confidence>=.8:return "high"
    if confidence>=.6:return "medium"
    return "low"
