"""Add idempotent Booking change receipts."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0013"
down_revision = "20260717_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "booking_change_receipts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("booking_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
    )


def downgrade() -> None:
    op.drop_table("booking_change_receipts")
