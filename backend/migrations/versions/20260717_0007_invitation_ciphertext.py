"""Store encrypted retrievable Invitation Link material."""

from alembic import op
import sqlalchemy as sa

revision = "20260717_0007"
down_revision = "20260717_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("invitations") as batch_op:
        batch_op.add_column(sa.Column("token_ciphertext", sa.LargeBinary()))


def downgrade() -> None:
    with op.batch_alter_table("invitations") as batch_op:
        batch_op.drop_column("token_ciphertext")
