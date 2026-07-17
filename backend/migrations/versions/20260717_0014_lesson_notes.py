"""Add one publishable Lesson Note per Booking."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0014"
down_revision = "20260717_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lesson_notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("booking_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("markdown_source", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
    )


def downgrade() -> None:
    op.drop_table("lesson_notes")
