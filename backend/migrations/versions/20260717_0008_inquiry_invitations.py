"""Link Invitations created from Inquiries."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0008"
down_revision = "20260717_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("invitations") as batch_op:
        batch_op.add_column(sa.Column("inquiry_id", sa.String(length=36)))
        batch_op.create_foreign_key(
            "fk_invitations_inquiry_id", "inquiries", ["inquiry_id"], ["id"]
        )
        batch_op.create_unique_constraint(
            "uq_invitations_inquiry_id", ["inquiry_id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("invitations") as batch_op:
        batch_op.drop_constraint("uq_invitations_inquiry_id", type_="unique")
        batch_op.drop_constraint("fk_invitations_inquiry_id", type_="foreignkey")
        batch_op.drop_column("inquiry_id")
