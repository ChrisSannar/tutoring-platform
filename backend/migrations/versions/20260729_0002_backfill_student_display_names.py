"""Backfill display names for directly bootstrapped Students."""

from alembic import op

revision = "20260729_0002"
down_revision = "20260725_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE accounts SET display_name = email "
        "WHERE role = 'student' AND display_name IS NULL"
    )


def downgrade() -> None:
    pass
