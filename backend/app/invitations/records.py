from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, text

def create_draft_invitation(
    database_url: str,
    email: str,
    display_name: str,
    shared_personal_message: str,
    private_tutor_note: str,
) -> dict[str, str]:
    invitation = {
        "id": str(uuid4()),
        "email": email.strip().lower(),
        "display_name": display_name,
        "shared_personal_message": shared_personal_message,
        "private_tutor_note": private_tutor_note,
        "status": "draft",
    }
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO invitations "
                    "(id, email, display_name, shared_personal_message, "
                    "private_tutor_note, status, token_hash, expires_at) "
                    "VALUES (:id, :email, :display_name, :shared_personal_message, "
                    ":private_tutor_note, :status, NULL, NULL)"
                ),
                invitation,
            )
        return invitation
    finally:
        engine.dispose()

def get_tutor_invitation(
    database_url: str, invitation_id: str
) -> dict[str, str | datetime | None] | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            invitation = connection.execute(
                text(
                    "SELECT id, email, display_name, shared_personal_message, "
                    "private_tutor_note, status, expires_at FROM invitations "
                    "WHERE id = :id"
                ),
                {"id": invitation_id},
            ).mappings().first()
            return dict(invitation) if invitation is not None else None
    finally:
        engine.dispose()
