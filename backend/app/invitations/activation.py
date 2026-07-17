from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets

from sqlalchemy import create_engine, text

def _change_invitation_token(
    database_url: str, invitation_id: str, ttl_seconds: int, required_status: str
) -> dict[str, str | datetime] | None:
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            changed = connection.execute(
                text(
                    "UPDATE invitations SET status = 'active', token_hash = :token_hash, "
                    "expires_at = :expires_at WHERE id = :id AND status = :status"
                ),
                {
                    "id": invitation_id,
                    "status": required_status,
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "expires_at": expires_at,
                },
            )
            if changed.rowcount != 1:
                return None
        return {
            "id": invitation_id,
            "status": "active",
            "invitation_url": f"/invite/{raw_token}",
            "expires_at": expires_at,
        }
    finally:
        engine.dispose()

def activate_invitation(
    database_url: str, invitation_id: str, ttl_seconds: int
) -> dict[str, str | datetime] | None:
    return _change_invitation_token(database_url, invitation_id, ttl_seconds, "draft")

def regenerate_invitation(
    database_url: str, invitation_id: str, ttl_seconds: int
) -> dict[str, str | datetime] | None:
    return _change_invitation_token(database_url, invitation_id, ttl_seconds, "active")
