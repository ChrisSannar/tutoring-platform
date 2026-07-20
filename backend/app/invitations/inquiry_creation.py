from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.invitations.encryption import encrypt_invitation_token


def create_invitation_from_inquiry(
    database_url: str, inquiry_id: str, ttl_seconds: int, encryption_key: str
) -> dict[str, str | datetime] | None:
    raw_token = secrets.token_urlsafe(32)
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(seconds=ttl_seconds)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            inquiry = connection.execute(
                text(
                    "UPDATE inquiries SET status = 'invited' WHERE id = :id "
                    "AND status = 'new' RETURNING email"
                ),
                {"id": inquiry_id},
            ).mappings().first()
            if inquiry is None:
                return None
            invitation_id = str(uuid4())
            connection.execute(
                text(
                    "INSERT INTO invitations (id, inquiry_id, email, display_name, "
                    "shared_personal_message, private_tutor_note, status, token_hash, "
                    "token_ciphertext, created_at, expires_at) VALUES (:id, :inquiry_id, "
                    ":email, '', '', '', 'created', :token_hash, :ciphertext, "
                    ":created_at, :expires_at)"
                ),
                {
                    "id": invitation_id,
                    "inquiry_id": inquiry_id,
                    "email": inquiry["email"],
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "ciphertext": encrypt_invitation_token(raw_token, encryption_key),
                    "created_at": created_at,
                    "expires_at": expires_at,
                },
            )
            return {
                "id": invitation_id,
                "email": inquiry["email"],
                "status": "created",
                "invitation_url": f"/invite/{raw_token}",
                "expires_at": expires_at,
            }
    finally:
        engine.dispose()
