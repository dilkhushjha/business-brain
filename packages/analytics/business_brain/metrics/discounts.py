from __future__ import annotations
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from packages.shared.database.models import CustomerModel, SaleModel


def discount_anomalies(db: Session, business_id: UUID, days: int = 90, multiplier: float = 2.0, min_baseline_pct: float = 2.0, limit: int = 10) -> list[dict[str, Any]]:
    """Invoices whose discount rate is a material outlier vs. this
    business's own recent average -- not a fixed external threshold, since
    what counts as a normal discount varies a lot by trade (a hardware
    wholesaler and a clothing retailer have very different norms). Requires
    a real baseline (at least a handful of discounted invoices and an
    average discount rate that isn't itself negligible) before flagging
    anything, since "2x an almost-zero baseline" is still almost zero.

    discount_pct is computed against the pre-discount (gross) amount --
    total_amount is the net amount after discount, so gross = total_amount
    + discount_amount."""
    end = date.today(); start = end - timedelta(days=days - 1)
    rows = db.execute(
        select(SaleModel.invoice_number, SaleModel.discount_amount, SaleModel.total_amount, CustomerModel.name)
        .outerjoin(CustomerModel, CustomerModel.id == SaleModel.customer_id)
        .where(SaleModel.business_id == business_id, SaleModel.transaction_date.between(start, end),
               SaleModel.discount_amount > 0)
    ).all()

    discounted = []
    for invoice, discount, total, customer_name in rows:
        gross = Decimal(discount) + Decimal(total)
        if gross <= 0:
            continue
        discounted.append((invoice, customer_name, float(Decimal(discount) / gross * 100), float(discount)))

    if len(discounted) < 3:
        return []

    baseline = sum(pct for _, _, pct, _ in discounted) / len(discounted)
    if baseline < min_baseline_pct:
        return []

    result = []
    for invoice, customer_name, pct, discount_amount in discounted:
        if pct >= baseline * multiplier:
            result.append({
                "invoice_number": invoice,
                "customer": customer_name,
                "discount_pct": round(pct, 2),
                "baseline_discount_pct": round(baseline, 2),
                "discount_amount": discount_amount,
                "severity": "high" if pct >= baseline * 3 else "medium",
            })
    return sorted(result, key=lambda x: -x["discount_pct"])[:limit]
