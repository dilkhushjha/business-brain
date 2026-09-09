from decimal import Decimal

from sqlalchemy import select

from packages.data.business_brain.ingestion.expense_repository import persist_expenses
from packages.shared.database.models import ExpenseModel


def test_persist_expenses_creates_expense(db_session, seeder):
    business = seeder.business()
    rows = [{
        "transaction_date": "05-08-2026", "category": "Rent",
        "total_amount": "25000", "description": "August shop rent",
    }]

    created = persist_expenses(db_session, business.id, rows)
    db_session.commit()

    assert created == 1
    expense = db_session.execute(select(ExpenseModel).where(ExpenseModel.business_id == business.id)).scalar_one()
    assert expense.category == "Rent"
    assert expense.amount == Decimal("25000")


def test_persist_expenses_reconciles_by_external_id(db_session, seeder):
    business = seeder.business()
    first_pass = [{
        "transaction_date": "05-08-2026", "category": "Rent",
        "total_amount": "25000", "description": "August shop rent",
        "invoice_number": "EXP-1",
    }]
    persist_expenses(db_session, business.id, first_pass)
    db_session.commit()

    # Re-export with a corrected amount.
    second_pass = [{
        "transaction_date": "05-08-2026", "category": "Rent",
        "total_amount": "26000", "description": "August shop rent (corrected)",
        "invoice_number": "EXP-1",
    }]
    created = persist_expenses(db_session, business.id, second_pass)
    db_session.commit()

    assert created == 0  # reconciled, not counted as new
    expenses = db_session.execute(select(ExpenseModel).where(ExpenseModel.business_id == business.id)).scalars().all()
    assert len(expenses) == 1
    assert expenses[0].amount == Decimal("26000")


def test_persist_expenses_without_external_id_dedupes_on_exact_match(db_session, seeder):
    """No voucher number column in the source -- re-uploading the exact
    same file shouldn't create a duplicate expense."""
    business = seeder.business()
    rows = [{
        "transaction_date": "05-08-2026", "category": "Electricity",
        "total_amount": "3200", "description": "August electricity bill",
    }]

    first = persist_expenses(db_session, business.id, rows)
    db_session.commit()
    second = persist_expenses(db_session, business.id, rows)
    db_session.commit()

    assert first == 1
    assert second == 0
    expenses = db_session.execute(select(ExpenseModel).where(ExpenseModel.business_id == business.id)).scalars().all()
    assert len(expenses) == 1


def test_persist_expenses_without_external_id_creates_distinct_rows_for_different_expenses(db_session, seeder):
    business = seeder.business()
    rows = [
        {"transaction_date": "05-08-2026", "category": "Electricity", "total_amount": "3200", "description": "August bill"},
        {"transaction_date": "06-08-2026", "category": "Transport", "total_amount": "1500", "description": "Delivery fuel"},
    ]

    created = persist_expenses(db_session, business.id, rows)
    db_session.commit()

    assert created == 2
    expenses = db_session.execute(select(ExpenseModel).where(ExpenseModel.business_id == business.id)).scalars().all()
    assert len(expenses) == 2
