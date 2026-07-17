"""Add singleton Tutor business settings."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0010"
down_revision = "20260717_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    settings = op.create_table(
        "tutor_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("session_price_cents", sa.Integer(), nullable=False),
        sa.Column("tutor_timezone", sa.String(length=100), nullable=False),
        sa.Column("default_meeting_details", sa.Text()),
        sa.CheckConstraint("id = 1", name="ck_tutor_settings_singleton"),
        sa.CheckConstraint("currency = 'USD'", name="ck_tutor_settings_usd"),
        sa.CheckConstraint(
            "session_price_cents > 0", name="ck_tutor_settings_positive_price"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(
        settings,
        [
            {
                "id": 1,
                "currency": "USD",
                "session_price_cents": 7500,
                "tutor_timezone": "America/Chicago",
                "default_meeting_details": None,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("tutor_settings")
