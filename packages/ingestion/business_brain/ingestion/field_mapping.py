from dataclasses import dataclass
from difflib import SequenceMatcher


FIELD_ALIASES = {
    "date": {"date", "invoice_date", "bill_date", "transaction_date", "voucher_date"},
    "invoice_number": {"invoice", "invoice_no", "invoice_number", "bill_no", "voucher_no"},
    "customer": {"customer", "customer_name", "party", "party_name", "client"},
    "product": {"product", "product_name", "item", "item_name", "sku", "stock_item"},
    "quantity": {"qty", "quantity", "units", "units_sold"},
    "unit_price": {"price", "unit_price", "rate", "selling_price", "sale_rate"},
    "amount": {"amount", "sales", "sale_amount", "revenue", "value", "total"},
}


@dataclass(frozen=True)
class FieldMatch:
    source: str
    target: str
    score: float


def suggest_mapping(columns: list[str], minimum_score: float = 0.72) -> list[FieldMatch]:
    matches: list[FieldMatch] = []
    for column in columns:
        normalized = column.lower().strip().replace(" ", "_")
        best_target, best_score = None, 0.0
        for target, aliases in FIELD_ALIASES.items():
            for alias in aliases:
                score = SequenceMatcher(None, normalized, alias).ratio()
                if score > best_score:
                    best_target, best_score = target, score
        if best_target and best_score >= minimum_score:
            matches.append(FieldMatch(column, best_target, round(best_score, 3)))
    return matches
