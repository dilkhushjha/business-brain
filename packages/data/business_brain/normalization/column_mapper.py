from dataclasses import dataclass
import re


@dataclass(frozen=True)
class MappingCandidate:
    source_column: str
    canonical_field: str
    confidence: float


ALIASES: dict[str, tuple[str, ...]] = {
    "customer_name": ("customer", "customer name", "cust name", "party", "party name", "party ledger name", "buyer", "client"),
    "product_name": ("product", "product name", "item", "item name", "stock item", "stock item name", "item description"),
    "invoice_number": ("invoice", "invoice no", "invoice number", "bill no", "bill number", "voucher no", "voucher number"),
    "transaction_date": ("date", "invoice date", "bill date", "transaction date", "voucher date"),
    "quantity": ("qty", "quantity", "units", "nos", "no", "qty in pcs"),
    "unit_price": ("rate", "unit price", "selling price", "price", "sales rate"),
    "total_amount": ("amount", "total", "invoice amount", "sales amount", "net amount", "value", "net value"),
    "cost_price": ("cost", "cost price", "purchase rate", "buying price", "purchase value"),
    "discount_amount": ("discount", "discount amount", "disc", "disc amount", "less discount"),
    "due_date": ("due date", "payment due date", "due on", "credit due date", "bill due date"),
    "paid_amount": ("paid amount", "amount received", "received amount", "amount paid", "payment received"),
    "tax": ("tax", "gst", "tax amount", "gst amount", "total tax"),
    "cgst": ("cgst", "cgst amount"),
    "sgst": ("sgst", "sgst amount"),
    "igst": ("igst", "igst amount"),
    "taxable_value": ("taxable value", "taxable amount", "taxable"),
    "voucher_type": ("voucher type", "transaction type", "type"),
    "supplier_name": ("supplier", "supplier name", "vendor", "vendor name", "party supplier"),
}


def _clean(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", value.lower()).strip()


def suggest_mapping(columns: list[str], threshold: float = 0.80) -> list[MappingCandidate]:
    from rapidfuzz.fuzz import ratio

    candidates: list[MappingCandidate] = []
    used_fields: set[str] = set()
    for column in columns:
        cleaned = _clean(column)
        best_field, best_score = None, 0.0
        for field, aliases in ALIASES.items():
            score = max(ratio(cleaned, _clean(alias)) / 100 for alias in aliases)
            if score > best_score:
                best_field, best_score = field, score
        if best_field and best_score >= threshold:
            # Keep the strongest source column for each canonical field.
            if best_field in used_fields:
                continue
            candidates.append(MappingCandidate(column, best_field, round(best_score, 4)))
            used_fields.add(best_field)
    return candidates
