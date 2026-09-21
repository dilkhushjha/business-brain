from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session
from packages.analytics.business_brain.metrics.inventory import current_inventory_position, dead_stock, demand_spikes, inventory_signals, slow_moving_products, stock_risk
from packages.analytics.business_brain.integrity import audit_inventory_integrity
from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.models import InventoryMovementModel, ProductModel, PurchaseModel, SaleModel
from packages.shared.database.session import get_db
router=APIRouter(prefix="/inventory",tags=["analytics"])
@router.get("/{business_id}/signals")
def signals(business_id:UUID,days:int=30,limit:int=10,db:Session=Depends(get_db),_auth:dict=Depends(require_business_access)): return inventory_signals(db,business_id,days,limit)
@router.get("/{business_id}/slow-moving")
def slow_moving(business_id:UUID,days:int=30,threshold:float=40,limit:int=10,db:Session=Depends(get_db),_auth:dict=Depends(require_business_access)): return slow_moving_products(db,business_id,days,threshold,limit)
@router.get("/{business_id}/stock-risk")
def stock_risk_route(business_id:UUID,velocity_days:int=30,low_days_threshold:float=7,high_days_threshold:float=90,limit:int=10,db:Session=Depends(get_db),_auth:dict=Depends(require_business_access)): return stock_risk(db,business_id,velocity_days,low_days_threshold,high_days_threshold,limit=limit)
@router.get("/{business_id}/demand-spikes")
def demand_spikes_route(business_id:UUID,days:int=30,threshold:float=100,limit:int=10,db:Session=Depends(get_db),_auth:dict=Depends(require_business_access)): return demand_spikes(db,business_id,days,threshold,limit)
@router.get("/{business_id}/dead-stock")
def dead_stock_route(business_id:UUID,velocity_days:int=60,limit:int=10,db:Session=Depends(get_db),_auth:dict=Depends(require_business_access)): return dead_stock(db,business_id,velocity_days,limit=limit)


@router.get("/{business_id}/purchase-movements")
def purchase_movements(
    business_id: UUID,
    days: int = 30,
    limit: int = 10,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Show inventory units/cost entering the business through purchases.

    This is the purchase-side inventory ledger, not an estimate of stock on
    hand. Actual stock-on-hand remains driven by InventorySnapshotModel until
    sales/returns are also represented as inventory movements.
    """
    from datetime import date, timedelta
    end = date.today()
    start = end - timedelta(days=max(1, days) - 1)
    rows = db.execute(
        select(
            ProductModel.name,
            func.coalesce(func.sum(InventoryMovementModel.quantity), 0),
            func.coalesce(
                func.sum(InventoryMovementModel.quantity * InventoryMovementModel.unit_cost),
                0,
            ),
        )
        .join(ProductModel, ProductModel.id == InventoryMovementModel.product_id)
        .where(
            InventoryMovementModel.business_id == business_id,
            InventoryMovementModel.movement_type == "purchase",
            InventoryMovementModel.movement_date.between(start, end),
        )
        .group_by(ProductModel.id, ProductModel.name)
        .order_by(func.sum(InventoryMovementModel.quantity).desc())
        .limit(max(1, min(limit, 50)))
    ).all()
    return [
        {
            "name": row[0],
            "quantity_received": float(row[1]),
            "purchase_value": float(row[2]),
        }
        for row in rows
    ]


@router.get("/{business_id}/product-flow")
def product_flow(
    business_id: UUID,
    days: int = 30,
    limit: int = 10,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Connect purchased units, sold units and movement-derived balance."""
    from datetime import date, timedelta
    end = date.today()
    start = end - timedelta(days=max(1, days) - 1)
    rows = db.execute(
        select(
            ProductModel.id,
            ProductModel.name,
            func.coalesce(func.sum(
                case((InventoryMovementModel.movement_type == "purchase", InventoryMovementModel.quantity), else_=0)
            ), 0),
            func.coalesce(func.sum(
                case((InventoryMovementModel.movement_type == "sale", InventoryMovementModel.quantity), else_=0)
            ), 0),
        )
        .join(InventoryMovementModel, InventoryMovementModel.product_id == ProductModel.id)
        .where(
            ProductModel.business_id == business_id,
            InventoryMovementModel.business_id == business_id,
            InventoryMovementModel.movement_date.between(start, end),
            InventoryMovementModel.movement_type.in_(["purchase", "sale"]),
        )
        .group_by(ProductModel.id, ProductModel.name)
        .order_by(ProductModel.name)
        .limit(max(1, min(limit, 50)))
    ).all()
    return [
        {
            "name": row[1],
            "purchased": float(row[2]),
            "sold": float(row[3]),
            "movement_balance": float(row[2] - row[3]),
        }
        for row in rows
    ]


@router.get("/{business_id}/integrity")
def inventory_integrity(
    business_id: UUID,
    days: int = 3650,
    limit: int = 20,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Audit canonical purchase/sale lines against inventory movements."""
    return audit_inventory_integrity(db, business_id, days=days, limit=limit)


@router.get("/{business_id}/position")
def inventory_position(
    business_id: UUID,
    limit: int = 20,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    """Return current movement-derived stock position."""
    return current_inventory_position(db, business_id, limit=limit)
