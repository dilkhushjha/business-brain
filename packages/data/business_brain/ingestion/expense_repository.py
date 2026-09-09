from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.data.business_brain.ingestion.canonicalize import canonicalize_expense_row
from packages.shared.database.models import ExpenseModel


def persist_expenses(db: Session, business_id: UUID, rows: list[dict]) -> int:
    """Persist expenses. Unlike persist_sales()/persist_purchases(), there's
    no natural unique key here -- ExpenseModel.external_id has no unique
    constraint, and a real Tally expense/payment voucher export often has
    no distinct voucher number column at all, just date/ledger/amount/
    narration. Two dedup strategies depending on what's available:

    - If a row has external_id (e.g. a voucher number column was present
      and mapped), reconcile by (business_id, external_id): update the
      existing expense if found, matching the sales/purchase pattern.
    - If external_id is absent, dedupe by an exact match on
      (business_id, expense_date, category, amount, description) instead --
      not a strict identity guarantee (two genuinely different Rs 500 rent
      payments on the same day would collide), but re-uploading the same
      file twice is the case this actually needs to guard against, and an
      exact match on every field is a reasonable proxy for "this is the
      same row" without a real key to rely on.

    Returns the number of newly-created expenses.
    """
    created = 0
    for raw in rows:
        row = canonicalize_expense_row(raw)

        existing = None
        if row["external_id"]:
            existing = db.execute(
                select(ExpenseModel).where(
                    ExpenseModel.business_id == business_id,
                    ExpenseModel.external_id == row["external_id"],
                )
            ).scalar_one_or_none()
        else:
            existing = db.execute(
                select(ExpenseModel).where(
                    ExpenseModel.business_id == business_id,
                    ExpenseModel.expense_date == row["expense_date"],
                    ExpenseModel.category == row["category"],
                    ExpenseModel.amount == row["amount"],
                    ExpenseModel.description == row["description"],
                )
            ).scalar_one_or_none()

        if existing:
            if row["external_id"]:
                existing.expense_date = row["expense_date"]
                existing.category = row["category"]
                existing.amount = row["amount"]
                existing.description = row["description"]
            continue

        db.add(ExpenseModel(
            business_id=business_id,
            external_id=row["external_id"],
            expense_date=row["expense_date"],
            category=row["category"],
            amount=row["amount"],
            description=row["description"],
        ))
        created += 1

    return created
