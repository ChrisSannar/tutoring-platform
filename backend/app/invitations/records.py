from datetime import datetime
from sqlalchemy import create_engine, text

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
