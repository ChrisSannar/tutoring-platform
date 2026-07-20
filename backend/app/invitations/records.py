from datetime import datetime, timezone
from sqlalchemy import create_engine, text

from app.invitations.expiration import expire_due_by_id

def get_tutor_invitation(
    database_url: str, invitation_id: str
) -> dict[str, str | datetime | None] | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            expire_due_by_id(connection, invitation_id, datetime.now(timezone.utc))
            invitation = connection.execute(
                text(
                    "SELECT id, email, display_name, shared_personal_message, "
                    "private_tutor_note, status, created_at, first_opened_at, "
                    "claimed_at, expired_at, revoked_at, expires_at FROM invitations "
                    "WHERE id = :id"
                ),
                {"id": invitation_id},
            ).mappings().first()
            return dict(invitation) if invitation is not None else None
    finally:
        engine.dispose()
