from __future__ import annotations
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import InventoryMovementModel, InventorySnapshotModel, ProductModel, SaleLineModel, SaleModel

def inventory_signals(db: Session, business_id: UUID, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    end=date.today(); start=end-timedelta(days=days-1)
    rows=db.execute(select(ProductModel.name,SaleLineModel.quantity,SaleLineModel.unit_price).join(SaleLineModel,SaleLineModel.product_id==ProductModel.id).join(SaleModel,SaleModel.id==SaleLineModel.sale_id).where(ProductModel.business_id==business_id,SaleModel.business_id==business_id,SaleModel.transaction_date.between(start,end))).all()
    agg={}
    for name,q,p in rows:
        x=agg.setdefault(name,[Decimal("0"),Decimal("0")]);x[0]+=Decimal(q or 0);x[1]+=Decimal(q or 0)*Decimal(p or 0)
    out=[]
    for name,(qty,revenue) in agg.items():
        daily=qty/Decimal(days) if days else Decimal("0")
        out.append({"name":name,"units_sold":float(qty),"revenue":float(revenue),"avg_daily_units":round(float(daily),2),"signal":"fast_mover" if daily>=2 else "normal","recommended_review":"Prioritize replenishment" if daily>=2 else None})
    return sorted(out,key=lambda x:x["units_sold"],reverse=True)[:limit]


def slow_moving_products(db: Session, business_id: UUID, days: int = 30, threshold: float = 40, limit: int = 10) -> list[dict[str, Any]]:
    """Products whose sales velocity has dropped materially vs. the prior
    period of the same length. Approximates 'slow-moving inventory' from
    sales velocity alone, since this schema has no stock-on-hand tracking
    to compute true days-of-inventory-remaining."""
    end = date.today(); cur_start = end - timedelta(days=days - 1)
    prev_end = cur_start - timedelta(days=1); prev_start = prev_end - timedelta(days=days - 1)
    products = db.execute(select(ProductModel.id, ProductModel.name).where(ProductModel.business_id == business_id)).all()
    result = []
    for pid, name in products:
        def units_in(lo, hi):
            return float(db.scalar(
                select(func.coalesce(func.sum(SaleLineModel.quantity), 0))
                .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
                .where(SaleLineModel.product_id == pid, SaleModel.business_id == business_id,
                       SaleModel.transaction_date.between(lo, hi))
            ) or 0)
        cur = units_in(cur_start, end)
        prev = units_in(prev_start, prev_end)
        if prev and (prev - cur) / prev * 100 >= threshold:
            change_pct = round((cur - prev) / prev * 100, 2)
            result.append({
                "name": name, "current_units": cur, "previous_units": prev,
                "change_pct": change_pct,
                "severity": "high" if change_pct <= -70 else "medium",
            })
    return sorted(result, key=lambda x: x["change_pct"])[:limit]


def demand_spikes(db: Session, business_id: UUID, days: int = 30, threshold: float = 100, limit: int = 10) -> list[dict[str, Any]]:
    """Products whose sales velocity has increased materially vs. the
    prior period of the same length -- the symmetric opposite of
    slow_moving_products(), same current-vs-previous-window comparison.
    A sudden, large increase in demand is worth flagging on its own (stock
    may not keep pace, or it may signal something worth understanding --
    a promotion, a competitor stockout, a seasonal shift)."""
    end = date.today(); cur_start = end - timedelta(days=days - 1)
    prev_end = cur_start - timedelta(days=1); prev_start = prev_end - timedelta(days=days - 1)
    products = db.execute(select(ProductModel.id, ProductModel.name).where(ProductModel.business_id == business_id)).all()
    result = []
    for pid, name in products:
        def units_in(lo, hi):
            return float(db.scalar(
                select(func.coalesce(func.sum(SaleLineModel.quantity), 0))
                .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
                .where(SaleLineModel.product_id == pid, SaleModel.business_id == business_id,
                       SaleModel.transaction_date.between(lo, hi))
            ) or 0)
        cur = units_in(cur_start, end)
        prev = units_in(prev_start, prev_end)
        if prev and (cur - prev) / prev * 100 >= threshold:
            change_pct = round((cur - prev) / prev * 100, 2)
            result.append({
                "name": name, "current_units": cur, "previous_units": prev,
                "change_pct": change_pct,
                "severity": "high" if change_pct >= 200 else "medium",
            })
    return sorted(result, key=lambda x: -x["change_pct"])[:limit]


def _latest_snapshots(db: Session, business_id: UUID, snapshot_max_age_days: int) -> dict[Any, tuple[str, Decimal, date]]:
    """The most recent InventorySnapshot per product, within
    snapshot_max_age_days -- shared by stock_risk() and dead_stock() so
    both agree on what counts as "current stock" and what's too stale
    to trust."""
    snapshot_cutoff = date.today() - timedelta(days=snapshot_max_age_days)
    rows = db.execute(
        select(InventorySnapshotModel.product_id, ProductModel.name, InventorySnapshotModel.quantity, InventorySnapshotModel.snapshot_date)
        .join(ProductModel, ProductModel.id == InventorySnapshotModel.product_id)
        .where(InventorySnapshotModel.business_id == business_id, InventorySnapshotModel.snapshot_date >= snapshot_cutoff)
    ).all()
    latest: dict[Any, tuple[str, Decimal, date]] = {}
    for product_id, name, quantity, snapshot_date in rows:
        existing = latest.get(product_id)
        if existing is None or snapshot_date > existing[2]:
            latest[product_id] = (name, quantity, snapshot_date)
    return latest


def dead_stock(db: Session, business_id: UUID, velocity_days: int = 60, snapshot_max_age_days: int = 45, min_quantity: float = 1, limit: int = 10) -> list[dict[str, Any]]:
    """Products with a real, recent stock snapshot showing units on hand,
    but zero sales at all over a longer trailing window (60 days by
    default, longer than stock_risk()'s velocity window -- a product needs
    more time with no sales at all before "dead" is a fair call than it
    does to look merely slow). stock_risk() deliberately excludes
    zero-velocity products since a days-of-cover ratio isn't meaningful at
    zero velocity; this is that excluded case, named and detected on its
    own terms instead of silently dropped."""
    latest = _latest_snapshots(db, business_id, snapshot_max_age_days)
    velocity_end = date.today(); velocity_start = velocity_end - timedelta(days=velocity_days - 1)

    result = []
    for product_id, (name, quantity, snapshot_date) in latest.items():
        if quantity < min_quantity:
            continue
        units_sold = db.scalar(
            select(func.coalesce(func.sum(SaleLineModel.quantity), 0))
            .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
            .where(SaleLineModel.product_id == product_id, SaleModel.business_id == business_id,
                   SaleModel.transaction_date.between(velocity_start, velocity_end))
        ) or 0
        if units_sold > 0:
            continue
        result.append({
            "name": name, "quantity_on_hand": float(quantity),
            "snapshot_date": snapshot_date.isoformat(), "velocity_window_days": velocity_days,
        })
    return sorted(result, key=lambda x: -x["quantity_on_hand"])[:limit]


def stock_risk(db: Session, business_id: UUID, velocity_days: int = 30, low_days_threshold: float = 7, high_days_threshold: float = 90, snapshot_max_age_days: int = 45, limit: int = 10) -> dict[str, list[dict[str, Any]]]:
    """Real stock-on-hand risk, using an actual InventorySnapshot rather
    than the sales-velocity proxy slow_moving_products()/inventory_signals()
    use. For each product with a recent-enough snapshot (within
    snapshot_max_age_days -- a stale snapshot shouldn't drive a stockout/
    excess call), computes days_of_cover = current quantity / average daily
    sales velocity over the trailing velocity_days. Requires real velocity
    (> 0) to compute a meaningful days-of-cover ratio -- a product with zero
    recent sales isn't "excess" by this measure, see dead_stock() for that
    case instead.

    Returns {"stockout_risk": [...], "excess_inventory": [...]}.
    """
    velocity_end = date.today(); velocity_start = velocity_end - timedelta(days=velocity_days - 1)
    latest_by_product = _latest_snapshots(db, business_id, snapshot_max_age_days)

    stockout: list[dict[str, Any]] = []
    excess: list[dict[str, Any]] = []
    for product_id, (name, quantity, snapshot_date) in latest_by_product.items():
        units_sold = db.scalar(
            select(func.coalesce(func.sum(SaleLineModel.quantity), 0))
            .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
            .where(SaleLineModel.product_id == product_id, SaleModel.business_id == business_id,
                   SaleModel.transaction_date.between(velocity_start, velocity_end))
        ) or 0
        daily_velocity = Decimal(units_sold) / Decimal(velocity_days)
        if daily_velocity <= 0:
            continue
        days_of_cover = float(Decimal(quantity) / daily_velocity)

        if days_of_cover < low_days_threshold:
            stockout.append({
                "name": name, "quantity_on_hand": float(quantity),
                "avg_daily_units": round(float(daily_velocity), 2),
                "days_of_cover": round(days_of_cover, 1),
                "snapshot_date": snapshot_date.isoformat(),
                "severity": "high" if days_of_cover < low_days_threshold / 2 else "medium",
            })
        elif days_of_cover > high_days_threshold:
            excess.append({
                "name": name, "quantity_on_hand": float(quantity),
                "avg_daily_units": round(float(daily_velocity), 2),
                "days_of_cover": round(days_of_cover, 1),
                "snapshot_date": snapshot_date.isoformat(),
                "severity": "high" if days_of_cover > high_days_threshold * 2 else "medium",
            })

    stockout.sort(key=lambda x: x["days_of_cover"])
    excess.sort(key=lambda x: -x["days_of_cover"])
    return {"stockout_risk": stockout[:limit], "excess_inventory": excess[:limit]}


def current_inventory_position(db: Session, business_id: UUID, limit: int = 50) -> list[dict[str, Any]]:
    """Return movement-derived inventory position for products with a ledger."""
    rows = db.execute(
        select(
            ProductModel.id,
            ProductModel.name,
            func.coalesce(func.sum(
                case(
                    (InventoryMovementModel.movement_type.in_(["purchase", "return_in"]), InventoryMovementModel.quantity),
                    (InventoryMovementModel.movement_type.in_(["sale", "return_out"]), -InventoryMovementModel.quantity),
                    else_=0,
                )
            ), 0),
            func.coalesce(func.sum(
                case(
                    (InventoryMovementModel.movement_type.in_(["purchase", "return_in"]), InventoryMovementModel.quantity * InventoryMovementModel.unit_cost),
                    else_=0,
                )
            ), 0),
        )
        .join(InventoryMovementModel, InventoryMovementModel.product_id == ProductModel.id)
        .where(InventoryMovementModel.business_id == business_id, ProductModel.business_id == business_id)
        .group_by(ProductModel.id, ProductModel.name)
        .order_by(ProductModel.name)
        .limit(max(1, min(limit, 100)))
    ).all()
    return [
        {"name": name, "quantity_on_hand": float(quantity), "ledger_inventory_value": float(value), "source": "inventory_movement_ledger"}
        for _, name, quantity, value in rows
    ]


def negative_inventory_products(db: Session, business_id: UUID, limit: int = 10) -> list[dict[str, Any]]:
    """Return products whose movement ledger has more outbound than inbound units."""
    rows = db.execute(
        select(
            ProductModel.name,
            func.coalesce(
                func.sum(
                    case(
                        (InventoryMovementModel.movement_type.in_(["purchase", "return_in"]), InventoryMovementModel.quantity),
                        (InventoryMovementModel.movement_type.in_(["sale", "return_out"]), -InventoryMovementModel.quantity),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .join(InventoryMovementModel, InventoryMovementModel.product_id == ProductModel.id)
        .where(
            InventoryMovementModel.business_id == business_id,
            ProductModel.business_id == business_id,
        )
        .group_by(ProductModel.id, ProductModel.name)
        .having(
            func.sum(
                case(
                    (InventoryMovementModel.movement_type.in_(["purchase", "return_in"]), InventoryMovementModel.quantity),
                    (InventoryMovementModel.movement_type.in_(["sale", "return_out"]), -InventoryMovementModel.quantity),
                    else_=0,
                )
            ) < 0
        )
        .order_by(
            func.sum(
                case(
                    (InventoryMovementModel.movement_type.in_(["purchase", "return_in"]), InventoryMovementModel.quantity),
                    (InventoryMovementModel.movement_type.in_(["sale", "return_out"]), -InventoryMovementModel.quantity),
                    else_=0,
                )
            )
        )
        .limit(max(1, min(limit, 100)))
    ).all()
    return [
        {
            "name": name,
            "movement_balance": float(balance),
            "shortfall_units": float(-balance),
        }
        for name, balance in rows
    ]
