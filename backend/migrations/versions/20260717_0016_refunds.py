"""Add reviewed full-refund requests and evidence."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0016"
down_revision = "20260717_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refund_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("booking_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("student_account_id", sa.String(length=36), nullable=False),
        sa.Column("payment_evidence_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["student_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["payment_evidence_id"], ["payment_evidence.id"]),
        sa.UniqueConstraint("student_account_id", "idempotency_key"),
    )
    op.create_table(
        "refund_evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("refund_request_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("provider_refund_id", sa.String(length=200), nullable=False, unique=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["refund_request_id"], ["refund_requests.id"]),
    )


def downgrade() -> None:
    op.drop_table("refund_evidence")
    op.drop_table("refund_requests")
