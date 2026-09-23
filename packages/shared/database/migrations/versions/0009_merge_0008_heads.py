"""merge authentication and business onboarding migration branches

Revision ID: 0009_merge_0008_heads
Revises: 0008_auth_hardening, 0008_business_onboarding

This merge revision intentionally performs no schema work. The two 0008
revisions were created independently from 0007_situation_history, so Alembic
needs an explicit merge point before there is a single canonical head.
"""

revision = "0009_merge_0008_heads"
down_revision = ("0008_auth_hardening", "0008_business_onboarding")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
