"""Discard superseded Session Request pilot data without conversion."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0017"
down_revision = "20260717_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("session_requests")


def downgrade() -> None:
    op.create_table(
        "session_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_account_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("service", sa.String(length=200), nullable=False),
        sa.Column("preferred_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["student_account_id"], ["accounts.id"]),
        sa.UniqueConstraint("student_account_id", "idempotency_key"),
    )
