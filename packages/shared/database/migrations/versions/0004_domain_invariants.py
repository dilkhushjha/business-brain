"""enforce core SME domain invariants

Revision ID: 0004_domain_invariants
down_revision = 0003_core_sme_domain
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_domain_invariants"
down_revision = "0003_core_sme_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_customers_credit_limit",
        "customers",
        "credit_limit IS NULL OR credit_limit >= 0",
    )
    op.create_check_constraint(
        "ck_suppliers_credit_period",
        "suppliers",
        "credit_period_days IS NULL OR credit_period_days >= 0",
    )
    op.create_check_constraint(
        "ck_purchase_lines_quantity_positive",
        "purchase_lines",
        "quantity > 0",
    )
    op.create_check_constraint(
        "ck_purchase_lines_unit_cost_nonnegative",
        "purchase_lines",
        "unit_cost >= 0",
    )
    op.create_check_constraint(
        "ck_purchase_lines_tax_nonnegative",
        "purchase_lines",
        "tax_amount >= 0",
    )
    op.create_check_constraint(
        "ck_purchase_lines_discount_nonnegative",
        "purchase_lines",
        "discount_amount >= 0",
    )
    op.create_check_constraint(
        "ck_purchase_lines_net_nonnegative",
        "purchase_lines",
        "net_amount >= 0",
    )
    op.create_check_constraint(
        "ck_payments_exactly_one_counterparty",
        "payments",
        "(customer_id IS NOT NULL AND supplier_id IS NULL) OR "
        "(customer_id IS NULL AND supplier_id IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_inventory_snapshots_quantity_nonnegative",
        "inventory_snapshots",
        "quantity >= 0",
    )
    op.create_check_constraint(
        "ck_inventory_snapshots_value_nonnegative",
        "inventory_snapshots",
        "value >= 0",
    )
    op.create_check_constraint(
        "ck_inventory_movements_unit_cost",
        "inventory_movements",
        "unit_cost IS NULL OR unit_cost >= 0",
    )


def downgrade() -> None:
    for name, table in [
        ("ck_inventory_movements_unit_cost", "inventory_movements"),
        ("ck_inventory_snapshots_value_nonnegative", "inventory_snapshots"),
        ("ck_inventory_snapshots_quantity_nonnegative", "inventory_snapshots"),
        ("ck_payments_exactly_one_counterparty", "payments"),
        ("ck_purchase_lines_net_nonnegative", "purchase_lines"),
        ("ck_purchase_lines_discount_nonnegative", "purchase_lines"),
        ("ck_purchase_lines_tax_nonnegative", "purchase_lines"),
        ("ck_purchase_lines_unit_cost_nonnegative", "purchase_lines"),
        ("ck_purchase_lines_quantity_positive", "purchase_lines"),
        ("ck_suppliers_credit_period", "suppliers"),
        ("ck_customers_credit_limit", "customers"),
    ]:
        op.drop_constraint(name, table_name=table, type_="check")
