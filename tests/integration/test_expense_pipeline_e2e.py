from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from packages.data.business_brain.ingestion.expense_repository import persist_expenses
from packages.data.business_brain.ingestion.orchestrator import prepare_expense_file
from packages.shared.database.models import ExpenseModel


def test_expense_csv_with_no_voucher_number_column_is_accepted(db_session, seeder, tmp_path: Path):
    """The whole reason prepare_expense_file() exists separately from
    prepare_file(): a real Tally expense/payment voucher export commonly
    has no distinct voucher-number column at all, and prepare_file()'s
    validation rules hard-require invoice_number for every row. Confirms
    an expense file without one is NOT rejected."""
    business = seeder.business()
    csv_path = tmp_path / "expenses.csv"
    csv_path.write_text(
        "Date,Ledger,Amount,Narration\n"
        "05-08-2026,Rent,25000,August shop rent\n"
        "06-08-2026,Electricity,3200,August electricity bill\n",
        encoding="utf-8",
    )

    result, prepared = prepare_expense_file(csv_path)
    assert result.rows_read == 2
    assert result.rows_accepted == 2
    assert result.rows_rejected == 0

    created = persist_expenses(db_session, business.id, [row.values for row in prepared])
    db_session.commit()

    assert created == 2
    expenses = db_session.execute(select(ExpenseModel).where(ExpenseModel.business_id == business.id)).scalars().all()
    assert len(expenses) == 2
    categories = {e.category for e in expenses}
    assert categories == {"Rent", "Electricity"}
    rent = next(e for e in expenses if e.category == "Rent")
    assert rent.amount == Decimal("25000")


def test_expense_csv_would_be_rejected_by_the_sales_shaped_validator(tmp_path: Path):
    """Regression guard for the bug this whole feature works around: the
    same file, run through the generic prepare_file() instead, should be
    rejected -- proving prepare_expense_file()'s separate rule set is
    actually doing something, not a no-op duplicate."""
    from packages.data.business_brain.ingestion.orchestrator import prepare_file

    csv_path = tmp_path / "expenses.csv"
    csv_path.write_text(
        "Date,Ledger,Amount,Narration\n"
        "05-08-2026,Rent,25000,August shop rent\n",
        encoding="utf-8",
    )
    result, prepared = prepare_file(csv_path)
    assert result.rows_rejected == 1
    assert result.rows_accepted == 0


def test_csv_expense_produces_a_real_expense_spike_signal(db_session, seeder, tmp_path: Path):
    """Same proof pattern as every other signal added this session: a
    real expense-register CSV (no voucher number column, exactly the
    realistic case this feature exists for), through the actual production
    ingestion path, into a firing EXPENSE_SPIKE signal."""
    from datetime import date

    from packages.analytics.business_brain.signals.engine import detect_signals

    business = seeder.business()
    # Baseline: normal transport spend in the prior 30-day window.
    seeder.expense(business.id, days_ago=45, category="Transport", amount=Decimal("5000"))

    csv_path = tmp_path / "recent_expenses.csv"
    csv_path.write_text(
        "Date,Ledger,Amount,Narration\n"
        f"{date.today().strftime('%d-%m-%Y')},Transport,12000,Delivery fuel and rentals\n",
        encoding="utf-8",
    )
    _, prepared = prepare_expense_file(csv_path)
    persist_expenses(db_session, business.id, [row.values for row in prepared])
    db_session.commit()

    signals = detect_signals(db_session, business.id, date.today())
    expense_signals = [s for s in signals if s.code == "EXPENSE_SPIKE"]
    assert len(expense_signals) == 1
    assert expense_signals[0].evidence["category"] == "Transport"
