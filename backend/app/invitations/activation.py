from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets

from sqlalchemy import create_engine

from app.invitations.encryption import encrypt_invitation_token
from app.invitations.transitions import regenerate_by_id

def regenerate_invitation(
    database_url: str, invitation_id: str, ttl_seconds: int, encryption_key: str
) -> dict[str, str | datetime] | None:
    raw_token = secrets.token_urlsafe(32)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(seconds=ttl_seconds)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            status = regenerate_by_id(
                connection,
                invitation_id,
                sha256(raw_token.encode()).hexdigest(),
                encrypt_invitation_token(raw_token, encryption_key),
                created_at,
                expires_at,
            )
            if status is None:
                return None
            if status == "conflict":
                return {"id": invitation_id, "status": "conflict"}
            return {
                "id": invitation_id,
                "status": status,
                "invitation_url": f"/invite/{raw_token}",
                "expires_at": expires_at,
            }
    finally:
        engine.dispose()
