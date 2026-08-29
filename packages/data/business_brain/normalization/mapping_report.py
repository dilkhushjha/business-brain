from dataclasses import dataclass
from typing import Any

from packages.data.business_brain.normalization.column_mapper import MappingCandidate, suggest_mapping


@dataclass(frozen=True)
class MappingReport:
    candidates: list[MappingCandidate]
    unmapped_columns: list[str]
    overall_confidence: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "mappings": [
                {
                    "source_column": item.source_column,
                    "canonical_field": item.canonical_field,
                    "confidence": item.confidence,
                }
                for item in self.candidates
            ],
            "unmapped_columns": self.unmapped_columns,
            "overall_confidence": self.overall_confidence,
        }


def build_mapping_report(columns: list[str], threshold: float = 0.80) -> MappingReport:
    candidates = suggest_mapping(columns, threshold=threshold)
    mapped = {item.source_column for item in candidates}
    confidence = (
        round(sum(item.confidence for item in candidates) / len(candidates), 4)
        if candidates else 0.0
    )
    return MappingReport(
        candidates=candidates,
        unmapped_columns=[column for column in columns if column not in mapped],
        overall_confidence=confidence,
    )
