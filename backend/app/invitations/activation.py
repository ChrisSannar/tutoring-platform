from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets

from sqlalchemy import create_engine, text

from app.invitations.encryption import encrypt_invitation_token

def regenerate_invitation(
    database_url: str, invitation_id: str, ttl_seconds: int, encryption_key: str
) -> dict[str, str | datetime] | None:
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            changed = connection.execute(
                text(
                    "UPDATE invitations SET status = CASE WHEN status = 'active' "
                    "THEN 'active' ELSE 'created' END, token_hash = :token_hash, "
                    "token_ciphertext = :ciphertext, expires_at = :expires_at "
                    "WHERE id = :id AND status IN ('active', 'created', 'opened') "
                    "RETURNING status"
                ),
                {
                    "id": invitation_id,
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "ciphertext": encrypt_invitation_token(raw_token, encryption_key),
                    "expires_at": expires_at,
                },
            ).mappings().first()
            if changed is None:
                return None
            return {
                "id": invitation_id,
                "status": changed["status"],
                "invitation_url": f"/invite/{raw_token}",
                "expires_at": expires_at,
            }
    finally:
        engine.dispose()
