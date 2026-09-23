"""add business onboarding profile fields

Revision ID: 0008_business_onboarding
down_revision = 0007_situation_history
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_business_onboarding"
down_revision = "0007_situation_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "businesses",
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="INR"),
    )
    op.add_column(
        "businesses",
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Asia/Kolkata"),
    )
    op.add_column(
        "businesses",
        sa.Column("fiscal_year_start_month", sa.SmallInteger(), nullable=False, server_default="4"),
    )
    op.add_column(
        "businesses",
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "businesses",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Existing pilot businesses already have a usable profile. Do not block them
    # behind the new onboarding screen; new businesses start incomplete.
    op.execute(sa.text("UPDATE businesses SET onboarding_completed = TRUE"))


def downgrade() -> None:
    op.drop_column("businesses", "onboarding_completed_at")
    op.drop_column("businesses", "onboarding_completed")
    op.drop_column("businesses", "fiscal_year_start_month")
    op.drop_column("businesses", "timezone")
    op.drop_column("businesses", "currency_code")
