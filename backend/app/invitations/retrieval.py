from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from app.invitations.encryption import decrypt_invitation_token
from app.invitations.expiration import expire_due_by_id


def retrieve_invitation_link(
    database_url: str, invitation_id: str, encryption_key: str
) -> str | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            expire_due_by_id(connection, invitation_id, datetime.now(timezone.utc))
            invitation = connection.execute(
                text(
                    "SELECT token_ciphertext FROM invitations WHERE id = :id "
                    "AND status IN ('created', 'opened')"
                ),
                {"id": invitation_id},
            ).mappings().first()
            if invitation is None or invitation["token_ciphertext"] is None:
                return None
            raw_token = decrypt_invitation_token(
                invitation["token_ciphertext"], encryption_key
            )
            return f"/invite/{raw_token}" if raw_token is not None else None
    finally:
        engine.dispose()
