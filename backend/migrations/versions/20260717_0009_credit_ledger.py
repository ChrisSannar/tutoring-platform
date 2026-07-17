"""Add the immutable Credit Ledger."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0009"
down_revision = "20260717_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credit_ledger_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_account_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=500)),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )


def downgrade() -> None:
    op.drop_table("credit_ledger_entries")
