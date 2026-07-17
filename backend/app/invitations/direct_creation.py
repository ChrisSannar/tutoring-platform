from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.invitations.encryption import encrypt_invitation_token


def create_manual_invitation(
    database_url: str, email: str, ttl_seconds: int, encryption_key: str
) -> dict[str, str | datetime]:
    raw_token = secrets.token_urlsafe(32)
    invitation = {
        "id": str(uuid4()),
        "email": email.strip().lower(),
        "status": "created",
        "token_hash": sha256(raw_token.encode()).hexdigest(),
        "token_ciphertext": encrypt_invitation_token(raw_token, encryption_key),
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
    }
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO invitations (id, email, display_name, "
                    "shared_personal_message, private_tutor_note, status, token_hash, "
                    "token_ciphertext, expires_at) VALUES (:id, :email, '', '', '', "
                    ":status, :token_hash, :token_ciphertext, :expires_at)"
                ),
                invitation,
            )
    finally:
        engine.dispose()
    return {
        "id": invitation["id"],
        "email": invitation["email"],
        "status": invitation["status"],
        "invitation_url": f"/invite/{raw_token}",
        "expires_at": invitation["expires_at"],
    }
