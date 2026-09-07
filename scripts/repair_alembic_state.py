"""Repair Alembic state when an existing database has no migration history.

This handles databases created by older Business Brain versions (or manually)
where the schema exists but ``alembic_version`` was never populated. It
reconstructs the migration state from the schema and never drops application
data.
"""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from packages.shared.database.session import engine

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "packages" / "shared" / "database" / "migrations"

REV_0001 = "0001_initial_schema"
REV_0002 = "0002_receivables"
REV_0003 = "0003_core_sme_domain"
REV_0004 = "0004_domain_invariants"

BASE_TABLES = {
    "businesses",
    "customers",
    "products",
    "source_files",
    "sales",
    "sale_lines",
    "ingestion_runs",
}
CORE_DOMAIN_TABLES = {
    "suppliers",
    "purchases",
    "purchase_lines",
    "payments",
    "expenses",
    "inventory_snapshots",
    "inventory_movements",
}

INVARIANT_CONSTRAINTS = {
    "customers": {"ck_customers_credit_limit"},
    "suppliers": {"ck_suppliers_credit_period"},
    "purchase_lines": {
        "ck_purchase_lines_quantity_positive",
        "ck_purchase_lines_unit_cost_nonnegative",
        "ck_purchase_lines_tax_nonnegative",
        "ck_purchase_lines_discount_nonnegative",
        "ck_purchase_lines_net_nonnegative",
    },
    "payments": {"ck_payments_exactly_one_counterparty"},
    "inventory_snapshots": {
        "ck_inventory_snapshots_quantity_nonnegative",
        "ck_inventory_snapshots_value_nonnegative",
    },
    "inventory_movements": {"ck_inventory_movements_unit_cost"},
}


def _config() -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(MIGRATIONS))
    return config


def _stamp(revision: str) -> None:
    command.stamp(_config(), revision)
    print(f"Reconstructed Alembic state at {revision}.")


def _detect_revision(inspector) -> str:
    tables = set(inspector.get_table_names())

    missing_base = sorted(BASE_TABLES - tables)
    if missing_base:
        raise RuntimeError(
            "The database has no Alembic migration history and its base schema "
            "is incomplete. Missing tables: "
            + ", ".join(missing_base)
            + ". Restore/recreate the database rather than guessing or dropping data."
        )

    sales_columns = {column["name"] for column in inspector.get_columns("sales")}
    has_receivables = {"due_date", "paid_amount"}.issubset(sales_columns)

    missing_domain = sorted(CORE_DOMAIN_TABLES - tables)
    if missing_domain:
        return REV_0002 if has_receivables else REV_0001

    # All 0003 tables exist. Verify the columns introduced by 0003 before
    # treating the database as being at that revision.
    customer_columns = {column["name"] for column in inspector.get_columns("customers")}
    product_columns = {column["name"] for column in inspector.get_columns("products")}
    required_0003_columns = {"phone", "email", "credit_limit"}
    if not required_0003_columns.issubset(customer_columns) or "unit" not in product_columns:
        return REV_0002 if has_receivables else REV_0001

    # If every 0004 invariant is already present, the schema is at head.
    # Otherwise it is at 0003 and the normal upgrade will apply 0004.
    for table, required in INVARIANT_CONSTRAINTS.items():
        names = {item.get("name") for item in inspector.get_check_constraints(table)}
        if not required.issubset(names):
            return REV_0003

    return REV_0004


def repair() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "alembic_version" in tables:
        print("Alembic state already exists; nothing to repair.")
        return

    detected = _detect_revision(inspector)
    _stamp(detected)

    if detected != REV_0004:
        command.upgrade(_config(), "head")
        print("Applied remaining migrations through head.")
    else:
        print("Schema already matches the current migration head; no upgrade needed.")

    print("No tables or application data were dropped or recreated.")


if __name__ == "__main__":
    repair()
