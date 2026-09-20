"""add human user authentication and business membership

Revision ID: 0006_user_auth
down_revision = 0005_connector_registry
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_user_auth"
down_revision = "0005_connector_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("ux_users_username", "users", ["username"], unique=True)
    op.create_index("ux_users_email", "users", ["email"], unique=True, postgresql_where=sa.text("email IS NOT NULL"))
    op.create_index("ux_users_phone", "users", ["phone"], unique=True, postgresql_where=sa.text("phone IS NOT NULL"))

    op.create_table(
        "user_businesses",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("business_id", sa.Uuid(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="owner"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("user_id", "business_id"),
    )
    op.create_index("ix_user_businesses_business_id", "user_businesses", ["business_id"])


def downgrade() -> None:
    op.drop_index("ix_user_businesses_business_id", table_name="user_businesses")
    op.drop_table("user_businesses")
    op.drop_index("ux_users_phone", table_name="users")
    op.drop_index("ux_users_email", table_name="users")
    op.drop_index("ux_users_username", table_name="users")
    op.drop_table("users")
