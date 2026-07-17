"""Add Checkout expectations and immutable payment evidence."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0015"
down_revision = "20260717_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkout_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("provider_session_id", sa.String(length=200), nullable=False, unique=True),
        sa.Column("checkout_url", sa.Text(), nullable=False),
        sa.Column("student_account_id", sa.String(length=36), nullable=False),
        sa.Column("slot_hold_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("focus", sa.String(length=500)),
        sa.Column("meeting_details_snapshot", sa.Text()),
        sa.Column("tutor_timezone_snapshot", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_account_id"], ["accounts.id"]),
        sa.UniqueConstraint("student_account_id", "idempotency_key"),
    )
    op.create_table(
        "stripe_events",
        sa.Column("provider_event_id", sa.String(length=200), primary_key=True),
        sa.Column("outcome", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "payment_evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("booking_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("checkout_session_id", sa.String(length=200), nullable=False, unique=True),
        sa.Column("provider_payment_id", sa.String(length=200), nullable=False, unique=True),
        sa.Column("provider_event_id", sa.String(length=200), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
    )


def downgrade() -> None:
    op.drop_table("payment_evidence")
    op.drop_table("stripe_events")
    op.drop_table("checkout_sessions")
