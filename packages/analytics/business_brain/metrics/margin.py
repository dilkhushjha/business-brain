from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import (
    ProductModel,
    PurchaseLineModel,
    PurchaseModel,
    SaleLineModel,
    SaleModel,
)


def _weighted_average_cost(
    db: Session,
    business_id: UUID,
    product_id: UUID,
    sale_id: UUID,
) -> Decimal | None:
    """Resolve a defensible product cost from purchase evidence."""
    sale_date = db.scalar(
        select(SaleModel.transaction_date).where(SaleModel.id == sale_id)
    )
    if sale_date is None:
        return None

    qty, value = db.execute(
        select(
            func.coalesce(func.sum(PurchaseLineModel.quantity), 0),
            func.coalesce(
                func.sum(PurchaseLineModel.quantity * PurchaseLineModel.unit_cost),
                0,
            ),
        )
        .join(PurchaseModel, PurchaseModel.id == PurchaseLineModel.purchase_id)
        .where(
            PurchaseModel.business_id == business_id,
            PurchaseLineModel.product_id == product_id,
            PurchaseModel.transaction_date <= sale_date,
        )
    ).one()

    quantity = Decimal(qty or 0)
    if quantity <= 0:
        return None

    return Decimal(value or 0) / quantity


def margin_summary(
    db: Session,
    business_id: UUID,
    days: int = 30,
) -> dict[str, Any]:
    end = date.today()
    start = end - timedelta(days=days - 1)

    revenue = Decimal("0")
    cost = Decimal("0")
    covered = Decimal("0")

    rows = db.execute(
        select(
            SaleLineModel.sale_id,
            SaleLineModel.product_id,
            SaleLineModel.quantity,
            SaleLineModel.unit_price,
            SaleLineModel.cost_price,
        )
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
        .where(
            SaleModel.business_id == business_id,
            SaleModel.transaction_date.between(start, end),
        )
    ).all()

    for sale_id, product_id, quantity, unit_price, recorded_cost in rows:
        q = Decimal(quantity or 0)
        price = Decimal(unit_price or 0)
        line_revenue = q * price
        effective_cost = (
            Decimal(recorded_cost)
            if recorded_cost is not None
            else _weighted_average_cost(db, business_id, product_id, sale_id)
        )

        revenue += line_revenue

        if effective_cost is not None:
            covered += line_revenue
            cost += q * effective_cost

    profit = covered - cost
    gross_margin = (profit / covered * 100) if covered else None

    return {
        "days": days,
        "revenue": float(revenue),
        "cost": float(cost),
        "gross_profit": float(profit),
        "gross_margin_pct": round(float(gross_margin), 2)
        if gross_margin is not None
        else None,
        "cost_coverage_pct": round(float(covered / revenue * 100), 2)
        if revenue
        else 0,
    }


def low_margin_products(
    db: Session,
    business_id: UUID,
    days: int = 30,
    threshold: float = 10,
    limit: int = 10,
) -> list[dict[str, Any]]:
    end = date.today()
    start = end - timedelta(days=days - 1)

    rows = db.execute(
        select(
            ProductModel.name,
            SaleLineModel.product_id,
            SaleLineModel.sale_id,
            SaleLineModel.quantity,
            SaleLineModel.unit_price,
            SaleLineModel.cost_price,
        )
        .join(SaleLineModel, SaleLineModel.product_id == ProductModel.id)
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
        .where(
            ProductModel.business_id == business_id,
            SaleModel.business_id == business_id,
            SaleModel.transaction_date.between(start, end),
        )
    ).all()

    aggregate: dict[str, list[float]] = {}

    for name, product_id, sale_id, quantity, unit_price, recorded_cost in rows:
        effective_cost = (
            Decimal(recorded_cost)
            if recorded_cost is not None
            else _weighted_average_cost(db, business_id, product_id, sale_id)
        )
        if effective_cost is None:
            continue

        revenue = float(Decimal(quantity or 0) * Decimal(unit_price or 0))
        cost = float(Decimal(quantity or 0) * effective_cost)

        bucket = aggregate.setdefault(name, [0.0, 0.0])
        bucket[0] += revenue
        bucket[1] += cost

    output: list[dict[str, Any]] = []

    for name, (revenue, cost) in aggregate.items():
        margin = (revenue - cost) / revenue * 100 if revenue else 0
        if margin <= threshold:
            output.append(
                {
                    "name": name,
                    "revenue": round(revenue, 2),
                    "gross_profit": round(revenue - cost, 2),
                    "margin_pct": round(margin, 2),
                    "severity": "high" if margin < 0 else "medium",
                }
            )

    return sorted(output, key=lambda row: row["margin_pct"])[:limit]
