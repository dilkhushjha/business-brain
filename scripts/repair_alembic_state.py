"""Repair Alembic state when an existing database has no migration history.

This handles databases created by older Business Brain versions (or manually)
where the schema exists but ``alembic_version`` was never populated. It never
changes application data or drops tables.
"""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from packages.shared.database.session import engine

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "packages" / "shared" / "database" / "migrations"
HEAD = "0004_domain_invariants"

# Tables that must exist for the current schema to be considered complete.
REQUIRED_TABLES = {
    "businesses",
    "customers",
    "products",
    "source_files",
    "sales",
    "sale_lines",
    "ingestion_runs",
    "suppliers",
    "purchases",
    "purchase_lines",
    "payments",
    "expenses",
    "inventory_snapshots",
    "inventory_movements",
}


def repair() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "alembic_version" in tables:
        print("Alembic state already exists; nothing to repair.")
        return

    missing = sorted(REQUIRED_TABLES - tables)
    if missing:
        raise RuntimeError(
            "The database has no Alembic migration history and its schema is "
            "incomplete. Refusing to guess or drop data. Missing tables: "
            + ", ".join(missing)
            + ". Restore/recreate the database, or repair the schema before "
            "stamping it."
        )

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(MIGRATIONS))
    command.stamp(config, HEAD)
    print(f"Alembic state repaired: database stamped at {HEAD}.")
    print("No tables or application data were modified.")


if __name__ == "__main__":
    repair()
