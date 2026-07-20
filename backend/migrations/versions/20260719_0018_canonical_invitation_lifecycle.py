"""Canonicalize Invitation lifecycle states and evidence."""

from alembic import op
import sqlalchemy as sa

revision = "20260719_0018"
down_revision = "20260717_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("invitation_claim_tokens")
    with op.batch_alter_table("invitations") as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True)))
        batch_op.add_column(sa.Column("first_opened_at", sa.DateTime(timezone=True)))
        batch_op.add_column(sa.Column("claimed_at", sa.DateTime(timezone=True)))
        batch_op.add_column(sa.Column("expired_at", sa.DateTime(timezone=True)))
        batch_op.add_column(sa.Column("revoked_at", sa.DateTime(timezone=True)))

    # Historical lifecycle times were never stored. NULL preserves that fact; runtime
    # writes still record complete evidence for every new Invitation.
    op.execute(
        "UPDATE invitations SET status = 'expired', expired_at = CURRENT_TIMESTAMP, "
        "token_hash = NULL, token_ciphertext = NULL "
        "WHERE status IN ('active', 'created', 'opened') "
        "AND expires_at <= CURRENT_TIMESTAMP"
    )
    op.execute(
        "UPDATE invitations SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP, "
        "token_hash = NULL, token_ciphertext = NULL "
        "WHERE status IN ('active', 'created', 'opened') "
        "AND (expires_at IS NULL OR token_hash IS NULL OR token_ciphertext IS NULL)"
    )
    op.execute(
        "UPDATE invitations SET status = 'created' "
        "WHERE status = 'active'"
    )
    op.execute(
        "UPDATE invitations SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP, "
        "token_hash = NULL, token_ciphertext = NULL "
        "WHERE status NOT IN ('created', 'opened', 'claimed', 'expired', 'revoked') "
        "OR (status = 'claimed' AND claimed_account_id IS NULL)"
    )
    op.execute(
        "UPDATE invitations SET token_hash = NULL, token_ciphertext = NULL "
        "WHERE status IN ('claimed', 'expired', 'revoked')"
    )

    with op.batch_alter_table("invitations") as batch_op:
        batch_op.create_check_constraint(
            "ck_invitations_canonical_status",
            "status IN ('created', 'opened', 'claimed', 'expired', 'revoked')",
        )
        batch_op.create_check_constraint(
            "ck_invitations_opened_evidence",
            "status != 'opened' OR first_opened_at IS NOT NULL OR created_at IS NULL",
        )
        batch_op.create_check_constraint(
            "ck_invitations_claimed_evidence",
            "status != 'claimed' OR (claimed_account_id IS NOT NULL AND "
            "(claimed_at IS NOT NULL OR created_at IS NULL))",
        )
        batch_op.create_check_constraint(
            "ck_invitations_expired_evidence",
            "status != 'expired' OR expired_at IS NOT NULL OR created_at IS NULL",
        )
        batch_op.create_check_constraint(
            "ck_invitations_revoked_evidence",
            "status != 'revoked' OR revoked_at IS NOT NULL OR created_at IS NULL",
        )
        batch_op.create_check_constraint(
            "ck_invitations_terminal_tokens_erased",
            "status NOT IN ('claimed', 'expired', 'revoked') OR "
            "(token_hash IS NULL AND token_ciphertext IS NULL)",
        )


def downgrade() -> None:
    with op.batch_alter_table("invitations") as batch_op:
        batch_op.drop_constraint(
            "ck_invitations_terminal_tokens_erased", type_="check"
        )
        batch_op.drop_constraint("ck_invitations_revoked_evidence", type_="check")
        batch_op.drop_constraint("ck_invitations_expired_evidence", type_="check")
        batch_op.drop_constraint("ck_invitations_claimed_evidence", type_="check")
        batch_op.drop_constraint("ck_invitations_opened_evidence", type_="check")
        batch_op.drop_constraint("ck_invitations_canonical_status", type_="check")
        batch_op.drop_column("revoked_at")
        batch_op.drop_column("expired_at")
        batch_op.drop_column("claimed_at")
        batch_op.drop_column("first_opened_at")
        batch_op.drop_column("created_at")

    op.create_table(
        "invitation_claim_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invitation_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["invitation_id"], ["invitations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
