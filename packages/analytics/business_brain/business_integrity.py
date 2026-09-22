from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.data_quality import audit_data_quality
from packages.analytics.business_brain.financial_integrity import audit_financial_linkage
from packages.analytics.business_brain.integrity import audit_inventory_integrity


def audit_business_integrity(
    db: Session,
    business_id: UUID,
) -> dict[str, Any]:
    """Aggregate read-only integrity audits used to qualify Business Brain conclusions."""
    audits = {
        "data_quality": audit_data_quality(db, business_id),
        "inventory": audit_inventory_integrity(db, business_id),
        "financial": audit_financial_linkage(db, business_id),
    }

    attention = [
        name for name, result in audits.items()
        if result.get("status") == "attention_required"
    ]
    issue_count = sum(
        int((result.get("summary") or {}).get("issue_count", 0))
        for result in audits.values()
    )

    return {
        "status": "attention_required" if attention else "reconciled",
        "issue_count": issue_count,
        "affected_domains": attention,
        "audits": audits,
        "conclusion_note": (
            "Some conclusions may be affected by unresolved data-integrity issues."
            if attention
            else "No integrity exceptions were detected by the current audit rules."
        ),
    }
