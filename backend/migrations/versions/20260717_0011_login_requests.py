"""Add manually fulfilled Student login requests."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0011"
down_revision = "20260717_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "login_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("magic_link_token_id", sa.String(length=36)),
        sa.Column("dismissed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["magic_link_token_id"], ["magic_link_tokens.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("magic_link_token_id"),
    )
    op.create_index("ix_login_requests_account", "login_requests", ["account_id"])


def downgrade() -> None:
    op.drop_index("ix_login_requests_account", table_name="login_requests")
    op.drop_table("login_requests")
