"""Associate a claimed Invitation with its Student account."""

from alembic import op
import sqlalchemy as sa

revision = "20260715_0004"
down_revision = "20260715_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(length=200)))
    with op.batch_alter_table("invitations") as batch_op:
        batch_op.add_column(
            sa.Column("claimed_account_id", sa.String(length=36), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_invitations_claimed_account_id",
            "accounts",
            ["claimed_account_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_invitations_claimed_account_id", ["claimed_account_id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("invitations") as batch_op:
        batch_op.drop_constraint(
            "uq_invitations_claimed_account_id", type_="unique"
        )
        batch_op.drop_constraint(
            "fk_invitations_claimed_account_id", type_="foreignkey"
        )
        batch_op.drop_column("claimed_account_id")
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.drop_column("display_name")
