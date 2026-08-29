"""add receivable tracking to sales

Revision ID: 0002_receivables
down_revision = 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_receivables"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sales", sa.Column("due_date", sa.Date(), nullable=True))
    op.add_column("sales", sa.Column("paid_amount", sa.Numeric(18, 2), nullable=False, server_default="0"))
    op.create_index("ix_sales_due_date", "sales", ["due_date"])


def downgrade() -> None:
    op.drop_index("ix_sales_due_date", table_name="sales")
    op.drop_column("sales", "paid_amount")
    op.drop_column("sales", "due_date")
