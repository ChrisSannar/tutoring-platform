from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


def test_invitation_status_and_evidence_constraints(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'invitation-constraints.sqlite3'}"
    config = Config("backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role, display_name) VALUES "
                    "('claimed-account', 'claimed@example.com', 'student', 'Claimed')"
                )
            )
        for status, evidence in (
            ("active", ""),
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
