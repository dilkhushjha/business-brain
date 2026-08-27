from dataclasses import dataclass
import re


@dataclass(frozen=True)
class MappingCandidate:
    source_column: str
    canonical_field: str
    confidence: float


ALIASES: dict[str, tuple[str, ...]] = {
    "customer_name": ("customer", "customer name", "cust name", "party", "party name", "client"),
    "product_name": ("product", "product name", "item", "item name", "stock item"),
    "invoice_number": ("invoice", "invoice no", "invoice number", "bill no", "bill number"),
    "transaction_date": ("date", "invoice date", "bill date", "transaction date"),
    "quantity": ("qty", "quantity", "units", "nos"),
    "unit_price": ("rate", "unit price", "selling price", "price"),
    "total_amount": ("amount", "total", "invoice amount", "sales amount", "net amount"),
    "cost_price": ("cost", "cost price", "purchase rate", "buying price"),
}


def _clean(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", value.lower()).strip()


def suggest_mapping(columns: list[str], threshold: float = 0.80) -> list[MappingCandidate]:
    from rapidfuzz.fuzz import ratio

    candidates: list[MappingCandidate] = []
    for column in columns:
        cleaned = _clean(column)
        best_field, best_score = None, 0.0
        for field, aliases in ALIASES.items():
            score = max(ratio(cleaned, _clean(alias)) / 100 for alias in aliases)
            if score > best_score:
                best_field, best_score = field, score
        if best_field and best_score >= threshold:
            candidates.append(MappingCandidate(column, best_field, round(best_score, 4)))
    return candidates
