"""add core SME domain tables

Revision ID: 0003_core_sme_domain
down_revision = 0002_receivables
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_core_sme_domain"
down_revision = "0002_receivables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("phone", sa.String(64), nullable=True))
    op.add_column("customers", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("customers", sa.Column("credit_limit", sa.Numeric(18, 2), nullable=True))
    op.add_column("products", sa.Column("unit", sa.String(64), nullable=True))

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("credit_period_days", sa.Integer(), nullable=True),
        sa.UniqueConstraint("business_id", "external_id"),
    )
    op.create_index("ix_suppliers_business_id", "suppliers", ["business_id"])

    op.create_table(
        "purchases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id"), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("invoice_number", sa.String(255), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.UniqueConstraint("business_id", "invoice_number"),
    )
    op.create_index("ix_purchases_business_id", "purchases", ["business_id"])
    op.create_index("ix_purchases_supplier_id", "purchases", ["supplier_id"])
    op.create_index("ix_purchases_transaction_date", "purchases", ["transaction_date"])
    op.create_index("ix_purchases_due_date", "purchases", ["due_date"])

    op.create_table(
        "purchase_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("purchase_id", sa.Uuid(), sa.ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("net_amount", sa.Numeric(18, 2), nullable=False),
    )
    op.create_index("ix_purchase_lines_purchase_id", "purchase_lines", ["purchase_id"])
    op.create_index("ix_purchase_lines_product_id", "purchase_lines", ["product_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id"), nullable=True),
        sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id"), nullable=True),
        sa.Column("purchase_id", sa.Uuid(), sa.ForeignKey("purchases.id"), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.CheckConstraint("direction IN ('in', 'out')", name="ck_payments_direction"),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
    )
    op.create_index("ix_payments_business_id", "payments", ["business_id"])
    op.create_index("ix_payments_customer_id", "payments", ["customer_id"])
    op.create_index("ix_payments_supplier_id", "payments", ["supplier_id"])
    op.create_index("ix_payments_sale_id", "payments", ["sale_id"])
    op.create_index("ix_payments_purchase_id", "payments", ["purchase_id"])
    op.create_index("ix_payments_payment_date", "payments", ["payment_date"])

    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
    )
    op.create_index("ix_expenses_business_id", "expenses", ["business_id"])
    op.create_index("ix_expenses_external_id", "expenses", ["external_id"])
    op.create_index("ix_expenses_expense_date", "expenses", ["expense_date"])

    op.create_table(
        "inventory_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("value", sa.Numeric(18, 2), nullable=False),
        sa.UniqueConstraint("business_id", "product_id", "snapshot_date"),
    )
    op.create_index("ix_inventory_snapshots_business_id", "inventory_snapshots", ["business_id"])
    op.create_index("ix_inventory_snapshots_product_id", "inventory_snapshots", ["product_id"])
    op.create_index("ix_inventory_snapshots_snapshot_date", "inventory_snapshots", ["snapshot_date"])

    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("movement_date", sa.Date(), nullable=False),
        sa.Column("movement_type", sa.String(16), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.CheckConstraint(
            "movement_type IN ('purchase', 'sale', 'return_in', 'return_out', 'adjustment')",
            name="ck_inventory_movement_type",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_movement_quantity_positive"),
    )
    op.create_index("ix_inventory_movements_business_id", "inventory_movements", ["business_id"])
    op.create_index("ix_inventory_movements_product_id", "inventory_movements", ["product_id"])
    op.create_index("ix_inventory_movements_movement_date", "inventory_movements", ["movement_date"])


def downgrade() -> None:
    for table in [
        "inventory_movements",
        "inventory_snapshots",
        "expenses",
        "payments",
        "purchase_lines",
        "purchases",
        "suppliers",
    ]:
        op.drop_table(table)
    op.drop_column("products", "unit")
    op.drop_column("customers", "credit_limit")
    op.drop_column("customers", "email")
    op.drop_column("customers", "phone")
