from __future__ import annotations
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import ProductModel, PurchaseLineModel, PurchaseModel, SupplierModel


def supplier_concentration(db: Session, business_id: UUID, top_n: int = 5) -> dict[str, Any]:
    """Mirrors customer_risk.customer_concentration(), on the spend side:
    how much of total purchase spend is concentrated in a small number of
    suppliers -- a business over-reliant on one supplier has real risk if
    that supplier raises prices, has a stock-out, or the relationship sours."""
    rows = db.execute(select(SupplierModel.name, func.sum(PurchaseModel.total_amount).label("spend")).join(PurchaseModel, PurchaseModel.supplier_id == SupplierModel.id).where(PurchaseModel.business_id == business_id).group_by(SupplierModel.id, SupplierModel.name).order_by(func.sum(PurchaseModel.total_amount).desc())).all()
    total = sum(float(r.spend or 0) for r in rows)
    top = [{"name": r.name, "spend": float(r.spend or 0), "share_pct": round(float(r.spend or 0)/total*100, 2) if total else 0} for r in rows[:top_n]]
    top_share = round(sum(x["share_pct"] for x in top), 2)
    level = "high" if top_share >= 60 or (top and top[0]["share_pct"] >= 35) else "medium" if top_share >= 40 or (top and top[0]["share_pct"] >= 20) else "low"
    return {"total_spend": total, "top_suppliers": top, "top_n": top_n, "top_share_pct": top_share, "risk": level}


def supplier_price_increases(db: Session, business_id: UUID, days: int = 30, threshold: float = 15, limit: int = 10) -> list[dict[str, Any]]:
    """Products whose quantity-weighted average purchase cost from a given
    supplier has increased materially vs. the prior period of equal
    length -- the purchase-side mirror of customer_risk.declining_customers()'s
    current-vs-previous-window comparison, applied to unit_cost instead of
    revenue."""
    end = date.today(); cur_start = end - timedelta(days=days - 1)
    prev_end = cur_start - timedelta(days=1); prev_start = prev_end - timedelta(days=days - 1)

    def weighted_avg_cost(lo: date, hi: date) -> dict[tuple[str, str], Decimal]:
        rows = db.execute(
            select(SupplierModel.name, ProductModel.name, PurchaseLineModel.quantity, PurchaseLineModel.unit_cost)
            .join(PurchaseModel, PurchaseModel.id == PurchaseLineModel.purchase_id)
            .join(SupplierModel, SupplierModel.id == PurchaseModel.supplier_id)
            .join(ProductModel, ProductModel.id == PurchaseLineModel.product_id)
            .where(PurchaseModel.business_id == business_id, PurchaseModel.transaction_date.between(lo, hi))
        ).all()
        agg: dict[tuple[str, str], list[Decimal]] = {}
        for supplier_name, product_name, qty, cost in rows:
            key = (supplier_name, product_name)
            entry = agg.setdefault(key, [Decimal("0"), Decimal("0")])
            entry[0] += qty
            entry[1] += qty * cost
        return {key: (total_cost / total_qty if total_qty else Decimal("0")) for key, (total_qty, total_cost) in agg.items()}

    current = weighted_avg_cost(cur_start, end)
    previous = weighted_avg_cost(prev_start, prev_end)

    result = []
    for key, prev_cost in previous.items():
        cur_cost = current.get(key)
        if cur_cost is None or prev_cost <= 0:
            continue
        change_pct = (cur_cost - prev_cost) / prev_cost * 100
        if change_pct >= threshold:
            supplier_name, product_name = key
            result.append({
                "supplier": supplier_name,
                "product": product_name,
                "current_cost": float(cur_cost),
                "previous_cost": float(prev_cost),
                "change_pct": round(float(change_pct), 2),
                "severity": "high" if change_pct >= 30 else "medium",
            })
    return sorted(result, key=lambda x: -x["change_pct"])[:limit]
