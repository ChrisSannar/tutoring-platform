"""Add one-use Invitation Claim verification tokens."""

from alembic import op
import sqlalchemy as sa

revision = "20260715_0003"
down_revision = "20260715_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invitation_claim_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invitation_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["invitation_id"], ["invitations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )


def downgrade() -> None:
    op.drop_table("invitation_claim_tokens")
