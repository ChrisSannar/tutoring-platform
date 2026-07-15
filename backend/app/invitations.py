from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
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


def activate_invitation(
    database_url: str, invitation_id: str, ttl_seconds: int
) -> dict[str, str | datetime] | None:
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            activated = connection.execute(
                text(
                    "UPDATE invitations SET status = 'active', "
                    "token_hash = :token_hash, expires_at = :expires_at "
                    "WHERE id = :id AND status = 'draft'"
                ),
                {
                    "id": invitation_id,
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "expires_at": expires_at,
                },
            )
            if activated.rowcount != 1:
                return None
        return {
            "id": invitation_id,
            "status": "active",
            "invitation_url": f"/invite/{raw_token}",
            "expires_at": expires_at,
        }
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
