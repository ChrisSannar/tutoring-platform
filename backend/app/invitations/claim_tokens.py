from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text

def issue_invitation_claim_token(
    database_url: str,
    raw_invitation_token: str,
    email: str,
    ttl_seconds: int,
) -> str | None:
    now = datetime.now(timezone.utc)
    raw_claim_token = secrets.token_urlsafe(32)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            invitation = connection.execute(
                text(
                    "SELECT id FROM invitations WHERE token_hash = :token_hash "
                    "AND email = :email AND status IN ('active', 'created', 'opened') "
                    "AND expires_at > :now"
                ),
                {
                    "token_hash": sha256(raw_invitation_token.encode()).hexdigest(),
                    "email": email.strip().lower(),
                    "now": now,
                },
            ).mappings().first()
            if invitation is None:
                return None
            connection.execute(
                text(
                    "INSERT INTO invitation_claim_tokens "
                    "(id, invitation_id, token_hash, expires_at, consumed_at) "
                    "VALUES (:id, :invitation_id, :token_hash, :expires_at, NULL)"
                ),
                {
                    "id": str(uuid4()),
                    "invitation_id": invitation["id"],
                    "token_hash": sha256(raw_claim_token.encode()).hexdigest(),
                    "expires_at": now + timedelta(seconds=ttl_seconds),
                },
            )
            return raw_claim_token
    finally:
        engine.dispose()

def get_active_invitation_claim(
    database_url: str, raw_claim_token: str
) -> dict[str, str] | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            invitation = connection.execute(
                text(
                    "SELECT invitations.email, invitations.display_name "
                    "FROM invitation_claim_tokens JOIN invitations "
                    "ON invitations.id = invitation_claim_tokens.invitation_id "
                    "WHERE invitation_claim_tokens.token_hash = :token_hash "
                    "AND invitation_claim_tokens.consumed_at IS NULL "
                    "AND invitation_claim_tokens.expires_at > :now "
                    "AND invitations.status IN ('active', 'created', 'opened')"
                ),
                {
                    "token_hash": sha256(raw_claim_token.encode()).hexdigest(),
                    "now": datetime.now(timezone.utc),
                },
            ).mappings().first()
            return dict(invitation) if invitation is not None else None
    finally:
        engine.dispose()
