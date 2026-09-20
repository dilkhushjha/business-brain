"""add business situation history

Revision ID: 0007_situation_history
Revises: 0006_user_auth
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_situation_history"
down_revision = "0006_user_auth"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "business_situation_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("situation_code", sa.String(length=128), nullable=False),
        sa.Column("first_seen_at", sa.Date(), nullable=False),
        sa.Column("last_seen_at", sa.Date(), nullable=False),
        sa.Column("resolved_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("priority_score", sa.Numeric(10, 2), nullable=False),
        sa.Column("confidence", sa.Numeric(6, 4), nullable=False),
        sa.Column("last_title", sa.String(length=500), nullable=False),
        sa.Column("last_explanation", sa.Text(), nullable=False),
        sa.Column("last_evidence", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id", "situation_code", name="uq_situation_history_business_code"),
    )
    op.create_index(
        "ix_situation_history_business_status",
        "business_situation_history",
        ["business_id", "status"],
    )
    op.create_index(
        "ix_situation_history_business_last_seen",
        "business_situation_history",
        ["business_id", "last_seen_at"],
    )


def downgrade():
    op.drop_index("ix_situation_history_business_last_seen", table_name="business_situation_history")
    op.drop_index("ix_situation_history_business_status", table_name="business_situation_history")
    op.drop_table("business_situation_history")
