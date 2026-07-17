from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.invitations.errors import InvitationClaimConflict


def claim_direct_invitation(
    database_url: str,
    raw_token: str,
    display_name: str,
    inactivity_seconds: int,
    absolute_seconds: int,
    previous_session: str | None,
) -> dict[str, str] | None:
    now = datetime.now(timezone.utc)
    account_id = str(uuid4())
    raw_session, raw_csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            invitation = connection.execute(
                text(
                    "UPDATE invitations SET status = 'claimed', display_name = :name, "
                    "claimed_account_id = :account_id, token_hash = NULL, "
                    "token_ciphertext = NULL WHERE token_hash = :token_hash "
                    "AND status IN ('created', 'opened') AND expires_at > :now "
                    "RETURNING id, email, inquiry_id"
                ),
                {
                    "name": display_name,
                    "account_id": account_id,
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "now": now,
                },
            ).mappings().first()
            if invitation is None:
                return None
            connection.execute(
                text(
                    "INSERT INTO accounts (id, email, role, display_name) "
                    "VALUES (:id, :email, 'student', :name)"
                ),
                {"id": account_id, "email": invitation["email"], "name": display_name},
            )
            connection.execute(
                text(
                    "INSERT INTO credit_ledger_entries (id, student_account_id, "
                    "event_type, quantity, reason, idempotency_key, created_at) VALUES "
                    "(:id, :student, 'promotion_granted', 1, NULL, :key, :now)"
                ),
                {
                    "id": str(uuid4()),
                    "student": account_id,
                    "key": f"invitation:{invitation['id']}:promotion",
                    "now": now,
                },
            )
            if invitation["inquiry_id"] is not None:
                connection.execute(
                    text("UPDATE inquiries SET status = 'archived' WHERE id = :id"),
                    {"id": invitation["inquiry_id"]},
                )
            if previous_session is not None:
                connection.execute(
                    text(
                        "UPDATE authentication_sessions SET revoked_at = :now "
                        "WHERE session_hash = :session_hash AND revoked_at IS NULL"
                    ),
                    {"now": now, "session_hash": sha256(previous_session.encode()).hexdigest()},
                )
            connection.execute(
                text(
                    "INSERT INTO authentication_sessions (id, account_id, session_hash, "
                    "csrf_hash, inactive_expires_at, absolute_expires_at, revoked_at) "
                    "VALUES (:id, :account, :session, :csrf, :inactive, :absolute, NULL)"
                ),
                {
                    "id": str(uuid4()), "account": account_id,
                    "session": sha256(raw_session.encode()).hexdigest(),
                    "csrf": sha256(raw_csrf.encode()).hexdigest(),
                    "inactive": now + timedelta(seconds=inactivity_seconds),
                    "absolute": now + timedelta(seconds=absolute_seconds),
                },
            )
            return {"status": "claimed", "role": "student", "email": invitation["email"],
                    "display_name": display_name, "session": raw_session, "csrf_token": raw_csrf}
    except IntegrityError:
        raise InvitationClaimConflict from None
    finally:
        engine.dispose()
