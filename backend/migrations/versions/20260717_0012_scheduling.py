"""Add availability and scheduling resources."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0012"
down_revision = "20260717_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "availability_windows",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.String(length=5), nullable=False),
        sa.Column("end_time", sa.String(length=5), nullable=False),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6"),
        sa.CheckConstraint("start_time < end_time"),
    )
    op.create_table(
        "blocked_times",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=500)),
        sa.CheckConstraint("start_at < end_at"),
    )
    op.create_table(
        "tutor_overrides",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("warning", sa.String(length=500), nullable=False),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_account_id", sa.String(length=36), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("funding_kind", sa.String(length=24), nullable=False),
        sa.Column("focus", sa.String(length=500)),
        sa.Column("meeting_details_snapshot", sa.Text()),
        sa.Column("price_cents_snapshot", sa.Integer()),
        sa.Column("currency_snapshot", sa.String(length=3)),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_account_id"], ["accounts.id"]),
    )
    op.create_table(
        "slot_holds",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_account_id", sa.String(length=36), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_account_id"], ["accounts.id"]),
    )


def downgrade() -> None:
    op.drop_table("slot_holds")
    op.drop_table("bookings")
    op.drop_table("tutor_overrides")
    op.drop_table("blocked_times")
    op.drop_table("availability_windows")
