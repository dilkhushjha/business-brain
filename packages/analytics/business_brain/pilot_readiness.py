from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.analytics.business_brain.business_integrity import audit_business_integrity
from packages.shared.database.models import (
    BusinessModel,
    CustomerModel,
    ProductModel,
    PurchaseModel,
    SaleModel,
    SupplierModel,
)


def audit_pilot_readiness(
    db: Session,
    business_id: UUID,
    as_of: date,
) -> dict[str, Any]:
    """Return a read-only go/no-go assessment for onboarding a real SME.

    This is deliberately a readiness gate, not a business-performance score.
    It checks whether the imported business has enough canonical data and
    whether known integrity exceptions could materially weaken conclusions.
    """
    business = db.get(BusinessModel, business_id)
    if business is None:
        return {
            "status": "not_ready",
            "business": None,
            "checks": [{
                "code": "BUSINESS_NOT_FOUND",
                "status": "blocker",
                "message": "The requested business does not exist.",
            }],
            "blockers": ["BUSINESS_NOT_FOUND"],
            "warnings": [],
        }

    counts = {
        "sales": db.scalar(select(func.count(SaleModel.id)).where(SaleModel.business_id == business_id)) or 0,
        "purchases": db.scalar(select(func.count(PurchaseModel.id)).where(PurchaseModel.business_id == business_id)) or 0,
        "customers": db.scalar(select(func.count(CustomerModel.id)).where(CustomerModel.business_id == business_id)) or 0,
        "suppliers": db.scalar(select(func.count(SupplierModel.id)).where(SupplierModel.business_id == business_id)) or 0,
        "products": db.scalar(select(func.count(ProductModel.id)).where(ProductModel.business_id == business_id)) or 0,
    }

    checks: list[dict[str, Any]] = []

    if counts["sales"] == 0:
        checks.append({
            "code": "NO_SALES_DATA",
            "status": "blocker",
            "message": "Import sales history before using sales-driven Business Brain conclusions.",
        })
    else:
        checks.append({
            "code": "SALES_DATA_PRESENT",
            "status": "pass",
            "message": f"{counts['sales']} sales documents are available.",
        })

    if counts["purchases"] == 0:
        checks.append({
            "code": "NO_PURCHASE_DATA",
            "status": "warning",
            "message": "Purchase intelligence will be limited until purchase history is imported.",
        })
    else:
        checks.append({
            "code": "PURCHASE_DATA_PRESENT",
            "status": "pass",
            "message": f"{counts['purchases']} purchase documents are available.",
        })

    for key, code, label in [
        ("customers", "NO_CUSTOMER_MASTER", "customer"),
        ("suppliers", "NO_SUPPLIER_MASTER", "supplier"),
        ("products", "NO_PRODUCT_MASTER", "product"),
    ]:
        if counts[key] == 0:
            checks.append({
                "code": code,
                "status": "warning",
                "message": f"No {label} master records are available; related intelligence will be limited.",
            })
        else:
            checks.append({
                "code": f"{key.upper()}_MASTER_PRESENT",
                "status": "pass",
                "message": f"{counts[key]} {label} master records are available.",
            })

    integrity = audit_business_integrity(db, business_id)
    if integrity["status"] == "attention_required":
        checks.append({
            "code": "INTEGRITY_EXCEPTIONS",
            "status": "blocker",
            "message": integrity["conclusion_note"],
            "issue_count": integrity["issue_count"],
            "affected_domains": integrity["affected_domains"],
        })
    else:
        checks.append({
            "code": "INTEGRITY_RECONCILED",
            "status": "pass",
            "message": "Current data-quality, inventory, and financial linkage audits are reconciled.",
        })

    blockers = [check["code"] for check in checks if check["status"] == "blocker"]
    warnings = [check["code"] for check in checks if check["status"] == "warning"]

    return {
        "status": "not_ready" if blockers else ("ready_with_warnings" if warnings else "ready"),
        "business": {
            "id": business.id.hex,
            "name": business.name,
            "industry": business.industry,
        },
        "as_of": as_of.isoformat(),
        "counts": counts,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "pilot_rule": (
            "Ready means canonical sales data exists and current integrity audits "
            "are reconciled. Warnings indicate limited domains, not invalid data."
        ),
    }
