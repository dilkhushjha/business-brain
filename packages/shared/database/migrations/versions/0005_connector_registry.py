"""add connector registry

Revision ID: 0005_connector_registry
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_connector_registry"
down_revision = "0004_domain_invariants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_brain_connectors",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default="Business Brain Connector"),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("token_prefix", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("version", sa.String(32), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("ix_business_brain_connectors_business_id", "business_brain_connectors", ["business_id"])
    op.create_index("ix_business_brain_connectors_status", "business_brain_connectors", ["status"])


def downgrade() -> None:
    op.drop_index("ix_business_brain_connectors_status", table_name="business_brain_connectors")
    op.drop_index("ix_business_brain_connectors_business_id", table_name="business_brain_connectors")
    op.drop_table("business_brain_connectors")
