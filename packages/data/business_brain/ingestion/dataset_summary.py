from __future__ import annotations
from collections import Counter
from typing import Any

def summarize_import(rows:list[dict[str,Any]])->dict[str,Any]:
    dates=[str(r.get("transaction_date"))[:10] for r in rows if r.get("transaction_date")]
    customers=Counter(str(r.get("customer_name")) for r in rows if r.get("customer_name"))
    products=Counter(str(r.get("product_name")) for r in rows if r.get("product_name"))
    return {"rows":len(rows),"date_from":min(dates) if dates else None,"date_to":max(dates) if dates else None,"unique_customers":len(customers),"unique_products":len(products),"top_customers":[{"name":n,"rows":c} for n,c in customers.most_common(5)],"top_products":[{"name":n,"rows":c} for n,c in products.most_common(5)]}
