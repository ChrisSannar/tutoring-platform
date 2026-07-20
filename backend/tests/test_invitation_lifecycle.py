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
                    "INSERT INTO accounts (id, email, role, display_name) VALUES "
                    "('claimed-account', 'claimed@example.com', 'student', 'Claimed')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO invitations (id, email, display_name, "
                    "shared_personal_message, private_tutor_note, status, token_hash, "
                    "token_ciphertext, expires_at) VALUES "
                    "('draft', 'draft@example.com', '', '', '', 'draft', NULL, NULL, NULL), "
                    "('active', 'active@example.com', '', '', '', 'active', "
                    "'active-hash', X'01', '2099-07-26 12:00:00'), "
                    "('created', 'created@example.com', '', '', '', 'created', "
                    "'created-hash', X'03', '2099-07-26 12:00:00'), "
                    "('opened', 'opened@example.com', '', '', '', 'opened', "
                    "'opened-hash', X'04', '2099-07-26 12:00:00'), "
                    "('claimed', 'claimed@example.com', '', '', '', 'claimed', "
                    "'claimed-hash', X'05', '2099-07-26 12:00:00'), "
                    "('expired', 'expired@example.com', '', '', '', 'expired', "
                    "'expired-terminal-hash', X'06', '2000-01-01 00:00:00'), "
                    "('revoked', 'revoked@example.com', '', '', '', 'revoked', "
                    "'revoked-hash', X'07', '2099-07-26 12:00:00'), "
                    "('unknown', 'unknown@example.com', '', '', '', 'anything', "
                    "'unknown-hash', X'08', '2099-07-26 12:00:00'), "
                    "('incomplete-active', 'incomplete@example.com', '', '', '', "
                    "'active', 'incomplete-hash', NULL, '2099-07-26 12:00:00'), "
                    "('incomplete-claimed', 'incomplete-claimed@example.com', '', '', "
                    "'', 'claimed', 'incomplete-claimed-hash', X'09', "
                    "'2099-07-26 12:00:00'), "
                    "('expired-active', 'expired@example.com', '', '', '', 'active', "
                    "'expired-hash', X'02', '2000-01-01 00:00:00')"
                )
            )
            connection.execute(
                text(
                    "UPDATE invitations SET claimed_account_id = 'claimed-account' "
                    "WHERE id = 'claimed'"
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
        for status, evidence in (
            ("opened", ""),
            ("claimed", ", claimed_account_id"),
            ("expired", ""),
            ("revoked", ""),
        ):
            with pytest.raises(IntegrityError), engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO invitations (id, email, display_name, "
                        "shared_personal_message, private_tutor_note, status, "
                        f"created_at{evidence}) VALUES (:id, :email, '', '', '', "
                        f":status, CURRENT_TIMESTAMP{', :account' if evidence else ''})"
                    ),
                    {
                        "id": f"runtime-{status}",
                        "email": f"runtime-{status}@example.com",
                        "status": status,
                        "account": "claimed-account",
                    },
                )
    finally:
        engine.dispose()

    by_id = {row["id"]: row for row in invitations}
    assert by_id["active"]["status"] == "created"
    assert by_id["active"]["token_hash"] == "active-hash"
    assert by_id["active"]["token_ciphertext"] == b"\x01"
    assert by_id["active"]["created_at"] is None
    assert by_id["created"]["status"] == "created"
    assert by_id["created"]["created_at"] is None
    assert by_id["opened"]["status"] == "opened"
    assert by_id["opened"]["first_opened_at"] is None
    assert by_id["claimed"]["status"] == "claimed"
    assert by_id["claimed"]["claimed_at"] is None
    assert by_id["claimed"]["token_hash"] is None
    assert by_id["claimed"]["token_ciphertext"] is None
    assert by_id["expired"]["status"] == "expired"
    assert by_id["expired"]["expired_at"] is None
    assert by_id["expired"]["token_hash"] is None
    assert by_id["revoked"]["status"] == "revoked"
    assert by_id["revoked"]["revoked_at"] is None
    assert by_id["revoked"]["token_hash"] is None
    assert by_id["unknown"]["status"] == "revoked"
    assert by_id["unknown"]["revoked_at"] is not None
    assert by_id["unknown"]["token_hash"] is None
    assert by_id["draft"]["status"] == "revoked"
    assert by_id["draft"]["revoked_at"] is not None
    assert by_id["incomplete-active"]["status"] == "revoked"
    assert by_id["incomplete-active"]["token_hash"] is None
    assert by_id["incomplete-claimed"]["status"] == "revoked"
    assert by_id["incomplete-claimed"]["revoked_at"] is not None
    assert by_id["incomplete-claimed"]["token_hash"] is None
    assert by_id["expired-active"]["status"] == "expired"
    assert by_id["expired-active"]["expired_at"] is not None
    assert by_id["expired-active"]["token_hash"] is None
    assert by_id["expired-active"]["token_ciphertext"] is None
    assert all(row["created_at"] is None for row in invitations)
    assert claim_token_table_count == 0
