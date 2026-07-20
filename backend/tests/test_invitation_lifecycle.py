from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


def test_migration_canonicalizes_historical_invitations_and_retires_claim_tokens(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite:///{tmp_path / 'invitation-lifecycle.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "20260717_0017")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO invitations (id, email, display_name, "
                    "shared_personal_message, private_tutor_note, status, token_hash, "
                    "token_ciphertext, expires_at) VALUES "
                    "('draft', 'draft@example.com', '', '', '', 'draft', NULL, NULL, NULL), "
                    "('active', 'active@example.com', '', '', '', 'active', "
                    "'active-hash', X'01', '2099-07-26 12:00:00'), "
                    "('incomplete-active', 'incomplete@example.com', '', '', '', "
                    "'active', 'incomplete-hash', NULL, '2099-07-26 12:00:00'), "
                    "('expired-active', 'expired@example.com', '', '', '', 'active', "
                    "'expired-hash', X'02', '2000-01-01 00:00:00')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO invitation_claim_tokens "
                    "(id, invitation_id, token_hash, expires_at, consumed_at) VALUES "
                    "('claim-token', 'active', 'claim-hash', "
                    "'2099-07-26 12:00:00', NULL)"
                )
            )

        command.upgrade(config, "head")

        with engine.connect() as connection:
            invitations = connection.execute(
                text(
                    "SELECT id, status, token_hash, token_ciphertext, created_at, "
                    "first_opened_at, claimed_at, expired_at, revoked_at "
                    "FROM invitations ORDER BY id"
                )
            ).mappings().all()
            claim_token_table_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'invitation_claim_tokens'"
                )
            ).scalar_one()
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO invitations (id, email, display_name, "
                    "shared_personal_message, private_tutor_note, status, created_at) "
                    "VALUES ('legacy-runtime', 'legacy@example.com', '', '', '', "
                    "'active', CURRENT_TIMESTAMP)"
                )
            )
    finally:
        engine.dispose()

    by_id = {row["id"]: row for row in invitations}
    assert by_id["active"]["status"] == "created"
    assert by_id["active"]["token_hash"] == "active-hash"
    assert by_id["active"]["token_ciphertext"] == b"\x01"
    assert by_id["active"]["created_at"] is not None
    assert by_id["draft"]["status"] == "revoked"
    assert by_id["draft"]["revoked_at"] is not None
    assert by_id["incomplete-active"]["status"] == "revoked"
    assert by_id["incomplete-active"]["token_hash"] is None
    assert by_id["expired-active"]["status"] == "expired"
    assert by_id["expired-active"]["expired_at"] is not None
    assert by_id["expired-active"]["token_hash"] is None
    assert by_id["expired-active"]["token_ciphertext"] is None
    assert all(row["created_at"] is not None for row in invitations)
    assert claim_token_table_count == 0
