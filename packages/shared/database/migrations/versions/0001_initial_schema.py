"""initial business brain schema

Revision ID: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "businesses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("external_id", sa.String(255)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.UniqueConstraint("business_id", "external_id"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("sku", sa.String(255)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(255)),
        sa.UniqueConstraint("business_id", "sku"),
    )
    op.create_table(
        "source_files",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("checksum", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("business_id", "checksum"),
    )
    op.create_table(
        "sales",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id")),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("invoice_number", sa.String(255), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False),
        sa.UniqueConstraint("business_id", "invoice_number"),
    )
    op.create_table(
        "sale_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("cost_price", sa.Numeric(18, 4)),
    )
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), sa.ForeignKey("source_files.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("rows_read", sa.Integer(), nullable=False),
        sa.Column("rows_accepted", sa.Integer(), nullable=False),
        sa.Column("rows_rejected", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text()),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
    )

    for table, column in [
        ("customers", "business_id"), ("products", "business_id"),
        ("source_files", "business_id"), ("sales", "business_id"),
        ("ingestion_runs", "business_id"), ("sales", "transaction_date"),
        ("sale_lines", "sale_id"), ("sale_lines", "product_id"),
        ("customers", "external_id"), ("products", "sku"),
    ]:
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    for table in ["ingestion_runs", "sale_lines", "sales", "source_files", "products", "customers", "businesses"]:
        op.drop_table(table)
