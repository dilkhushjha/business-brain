from __future__ import annotations
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from packages.shared.database.models import ExpenseModel


def expense_summary(db: Session, business_id: UUID, days: int = 30) -> dict[str, Any]:
    end = date.today(); start = end - timedelta(days=days - 1)
    rows = db.execute(
        select(ExpenseModel.category, func.sum(ExpenseModel.amount))
        .where(ExpenseModel.business_id == business_id, ExpenseModel.expense_date.between(start, end))
        .group_by(ExpenseModel.category)
    ).all()
    by_category = {category: float(total) for category, total in rows}
    return {"days": days, "total": sum(by_category.values()), "by_category": by_category}


def expense_spikes(db: Session, business_id: UUID, days: int = 30, threshold: float = 30, limit: int = 10) -> list[dict[str, Any]]:
    """Expense categories whose spend has increased materially vs. the
    prior period of equal length -- same current-vs-previous-window
    comparison shape as declining_customers()/supplier_price_increases(),
    applied to expense category totals. Requires real prior-period spend in
    that category (not zero) before flagging, same as the other signals in
    this family: a brand-new expense category has nothing to compare
    against, that's not a spike."""
    end = date.today(); cur_start = end - timedelta(days=days - 1)
    prev_end = cur_start - timedelta(days=1); prev_start = prev_end - timedelta(days=days - 1)

    def totals_in(lo: date, hi: date) -> dict[str, Decimal]:
        rows = db.execute(
            select(ExpenseModel.category, func.sum(ExpenseModel.amount))
            .where(ExpenseModel.business_id == business_id, ExpenseModel.expense_date.between(lo, hi))
            .group_by(ExpenseModel.category)
        ).all()
        return {category: Decimal(total) for category, total in rows}

    current = totals_in(cur_start, end)
    previous = totals_in(prev_start, prev_end)

    result = []
    for category, prev_total in previous.items():
        cur_total = current.get(category, Decimal("0"))
        if prev_total <= 0:
            continue
        change_pct = (cur_total - prev_total) / prev_total * 100
        if change_pct >= threshold:
            result.append({
                "category": category,
                "current_total": float(cur_total),
                "previous_total": float(prev_total),
                "change_pct": round(float(change_pct), 2),
                "severity": "high" if change_pct >= 75 else "medium",
            })
    return sorted(result, key=lambda x: -x["change_pct"])[:limit]
