from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from app.invitations.encryption import decrypt_invitation_token


def retrieve_invitation_link(
    database_url: str, invitation_id: str, encryption_key: str
) -> str | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            invitation = connection.execute(
                text(
                    "SELECT token_ciphertext, expires_at FROM invitations WHERE id = :id "
                    "AND status IN ('active', 'created', 'opened')"
                ),
                {"id": invitation_id},
            ).mappings().first()
            if invitation is None or invitation["token_ciphertext"] is None:
                return None
            raw_expires_at = invitation["expires_at"]
            expires_at = (
                datetime.fromisoformat(raw_expires_at)
                if isinstance(raw_expires_at, str)
                else raw_expires_at
            )
            if expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
                connection.execute(
                    text(
                        "UPDATE invitations SET status = 'expired', token_ciphertext = NULL "
                        "WHERE id = :id"
                    ),
                    {"id": invitation_id},
                )
                return None
            raw_token = decrypt_invitation_token(
                invitation["token_ciphertext"], encryption_key
            )
            return f"/invite/{raw_token}" if raw_token is not None else None
    finally:
        engine.dispose()
