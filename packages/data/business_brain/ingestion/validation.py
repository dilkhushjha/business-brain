from __future__ import annotations
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

REQUIRED=("invoice_number","transaction_date","customer_name","product_name","quantity","unit_price")

def validate_row(row:dict[str,Any],row_number:int)->tuple[dict[str,Any]|None,list[str]]:
    errors=[]
    for key in REQUIRED:
        if row.get(key) in (None,""):
            errors.append(f"{key} is required")
    if errors:return None,[f"row {row_number}: {e}" for e in errors]
    out=dict(row)
    try: out["quantity"]=Decimal(str(row["quantity"]))
    except (InvalidOperation,ValueError): errors.append("quantity must be numeric")
    try: out["unit_price"]=Decimal(str(row["unit_price"]))
    except (InvalidOperation,ValueError): errors.append("unit_price must be numeric")
    if row.get("total_amount") not in (None,""):
        try: out["total_amount"]=Decimal(str(row["total_amount"]))
        except (InvalidOperation,ValueError): errors.append("total_amount must be numeric")
    try:
        value=row["transaction_date"]
        if isinstance(value,date): out["transaction_date"]=value
        else: out["transaction_date"]=date.fromisoformat(str(value)[:10])
    except (ValueError,TypeError): errors.append("transaction_date must be YYYY-MM-DD or a date value")
    return (out,None) if not errors else (None,[f"row {row_number}: {e}" for e in errors])
