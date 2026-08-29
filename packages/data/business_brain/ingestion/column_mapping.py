from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class ColumnMapping:
    canonical: str
    source: str
    confidence: float

ALIASES={
    "invoice_number":["invoice","invoice no","invoice number","bill no","bill number","voucher no","voucher number"],
    "transaction_date":["date","invoice date","bill date","voucher date","transaction date"],
    "customer_name":["customer","customer name","party","party name","ledger name","buyer"],
    "product_name":["product","product name","item","item name","stock item","stock item name"],
    "quantity":["quantity","qty","units"],
    "unit_price":["unit price","rate","price","selling price"],
    "total_amount":["amount","total","total amount","invoice amount","sales amount","net amount"],
    "tax_amount":["tax","tax amount","gst","gst amount","cgst","sgst","igst"],
    "discount_amount":["discount","discount amount"],
    "due_date":["due date","due","payment due date"],
    "paid_amount":["paid","paid amount","amount paid","received","received amount"],
    "sku":["sku","item code","stock code","product code"],
}

def _norm(value:str)->str:
    return re.sub(r"[^a-z0-9]+"," ",value.lower()).strip()

def suggest_mapping(columns:list[str])->list[ColumnMapping]:
    normalized={_norm(c):c for c in columns}; out=[]
    for canonical,aliases in ALIASES.items():
        best=None
        for alias in aliases:
            key=_norm(alias)
            if key in normalized: best=(normalized[key],1.0);break
        if best: out.append(ColumnMapping(canonical,best[0],best[1]))
    return out
