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


def get_active_invitation_by_token(
    database_url: str, raw_token: str
) -> dict[str, str] | None:
    token_hash = sha256(raw_token.encode()).hexdigest()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE invitations SET status = 'expired' "
                    "WHERE token_hash = :token_hash AND status = 'active' "
                    "AND expires_at <= CURRENT_TIMESTAMP"
                ),
                {"token_hash": token_hash},
            )
            invitation = connection.execute(
                text(
                    "SELECT email, display_name, shared_personal_message "
                    "FROM invitations WHERE token_hash = :token_hash "
                    "AND status = 'active' AND expires_at > CURRENT_TIMESTAMP"
                ),
                {"token_hash": token_hash},
            ).mappings().first()
            return dict(invitation) if invitation is not None else None
    finally:
        engine.dispose()


def issue_invitation_claim_token(
    database_url: str,
    raw_invitation_token: str,
    email: str,
    ttl_seconds: int,
) -> str | None:
    normalized_email = email.strip().lower()
    now = datetime.now(timezone.utc)
    raw_claim_token = secrets.token_urlsafe(32)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            invitation = connection.execute(
                text(
                    "SELECT id FROM invitations WHERE token_hash = :token_hash "
                    "AND email = :email AND status = 'active' AND expires_at > :now"
                ),
                {
                    "token_hash": sha256(raw_invitation_token.encode()).hexdigest(),
                    "email": normalized_email,
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
                    "AND invitations.status = 'active'"
                ),
                {
                    "token_hash": sha256(raw_claim_token.encode()).hexdigest(),
                    "now": datetime.now(timezone.utc),
                },
            ).mappings().first()
            return dict(invitation) if invitation is not None else None
    finally:
        engine.dispose()


def claim_invitation(
    database_url: str,
    raw_claim_token: str,
    display_name: str,
    inactivity_seconds: int,
    absolute_seconds: int,
) -> dict[str, str] | None:
    now = datetime.now(timezone.utc)
    account_id = str(uuid4())
    raw_session = secrets.token_urlsafe(32)
    raw_csrf = secrets.token_urlsafe(32)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            claim = connection.execute(
                text(
                    "SELECT invitation_claim_tokens.id AS claim_token_id, "
                    "invitations.id AS invitation_id, invitations.email "
                    "FROM invitation_claim_tokens JOIN invitations "
                    "ON invitations.id = invitation_claim_tokens.invitation_id "
                    "WHERE invitation_claim_tokens.token_hash = :token_hash "
                    "AND invitation_claim_tokens.consumed_at IS NULL "
                    "AND invitation_claim_tokens.expires_at > :now "
                    "AND invitations.status = 'active'"
                ),
                {
                    "token_hash": sha256(raw_claim_token.encode()).hexdigest(),
                    "now": now,
                },
            ).mappings().first()
            if claim is None:
                return None
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role, display_name) "
                    "VALUES (:id, :email, 'student', :display_name)"
                ),
                {
                    "id": account_id,
                    "email": claim["email"],
                    "display_name": display_name,
                },
            )
            claimed = connection.execute(
                text(
                    "UPDATE invitations SET status = 'claimed', "
                    "display_name = :display_name, claimed_account_id = :account_id, "
                    "token_hash = NULL WHERE id = :invitation_id AND status = 'active'"
                ),
                {
                    "display_name": display_name,
                    "account_id": account_id,
                    "invitation_id": claim["invitation_id"],
                },
            )
            if claimed.rowcount != 1:
                return None
            connection.execute(
                text(
                    "UPDATE invitation_claim_tokens SET consumed_at = :now "
                    "WHERE id = :id AND consumed_at IS NULL"
                ),
                {"now": now, "id": claim["claim_token_id"]},
            )
            connection.execute(
                text(
                    "INSERT INTO authentication_sessions "
                    "(id, account_id, session_hash, csrf_hash, inactive_expires_at, "
                    "absolute_expires_at, revoked_at) VALUES "
                    "(:id, :account_id, :session_hash, :csrf_hash, "
                    ":inactive_expires_at, :absolute_expires_at, NULL)"
                ),
                {
                    "id": str(uuid4()),
                    "account_id": account_id,
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                    "csrf_hash": sha256(raw_csrf.encode()).hexdigest(),
                    "inactive_expires_at": now + timedelta(seconds=inactivity_seconds),
                    "absolute_expires_at": now + timedelta(seconds=absolute_seconds),
                },
            )
            return {
                "status": "claimed",
                "role": "student",
                "email": claim["email"],
                "display_name": display_name,
                "session": raw_session,
                "csrf_token": raw_csrf,
            }
    finally:
        engine.dispose()


def correct_invitation_email(
    database_url: str, invitation_id: str, email: str
) -> dict[str, str] | None:
    normalized_email = email.strip().lower()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            corrected = connection.execute(
                text(
                    "UPDATE invitations SET email = :email WHERE id = :id "
                    "AND status IN ('draft', 'active') RETURNING id, email, status"
                ),
                {"id": invitation_id, "email": normalized_email},
            ).mappings().first()
            return dict(corrected) if corrected is not None else None
    finally:
        engine.dispose()


def revoke_invitation(database_url: str, invitation_id: str) -> dict[str, str] | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            revoked = connection.execute(
                text(
                    "UPDATE invitations SET status = 'revoked' WHERE id = :id "
                    "AND status = 'active' RETURNING id, status"
                ),
                {"id": invitation_id},
            ).mappings().first()
            return dict(revoked) if revoked is not None else None
    finally:
        engine.dispose()


def regenerate_invitation(
    database_url: str, invitation_id: str, ttl_seconds: int
) -> dict[str, str | datetime] | None:
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            regenerated = connection.execute(
                text(
                    "UPDATE invitations SET token_hash = :token_hash, "
                    "expires_at = :expires_at WHERE id = :id AND status = 'active'"
                ),
                {
                    "id": invitation_id,
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "expires_at": expires_at,
                },
            )
            if regenerated.rowcount != 1:
                return None
        return {
            "id": invitation_id,
            "status": "active",
            "invitation_url": f"/invite/{raw_token}",
            "expires_at": expires_at,
        }
    finally:
        engine.dispose()
