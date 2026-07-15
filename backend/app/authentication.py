from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text


def accept_magic_link_request(database_url: str, email: str, ip_address: str) -> bool:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=1)
    email_hash = sha256(email.strip().lower().encode()).hexdigest()
    ip_hash = sha256(ip_address.encode()).hexdigest()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            counts = connection.execute(
                text(
                    "SELECT "
                    "SUM(CASE WHEN email_hash = :email_hash THEN 1 ELSE 0 END) "
                    "AS email_count, "
                    "SUM(CASE WHEN ip_hash = :ip_hash THEN 1 ELSE 0 END) "
                    "AS ip_count FROM authentication_request_events "
                    "WHERE requested_at >= :window_start"
                ),
                {
                    "email_hash": email_hash,
                    "ip_hash": ip_hash,
                    "window_start": window_start,
                },
            ).mappings().one()
            if (counts["email_count"] or 0) >= 5 or (counts["ip_count"] or 0) >= 20:
                return False
            connection.execute(
                text(
                    "INSERT INTO authentication_request_events "
                    "(id, email_hash, ip_hash, requested_at) "
                    "VALUES (:id, :email_hash, :ip_hash, :requested_at)"
                ),
                {
                    "id": str(uuid4()),
                    "email_hash": email_hash,
                    "ip_hash": ip_hash,
                    "requested_at": now,
                },
            )
            return True
    finally:
        engine.dispose()


def issue_magic_link(database_url: str, email: str, ttl_seconds: int) -> str | None:
    normalized_email = email.strip().lower()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            account = connection.execute(
                text("SELECT id FROM accounts WHERE email = :email"),
                {"email": normalized_email},
            ).mappings().first()
            if account is None:
                return None

            raw_token = secrets.token_urlsafe(32)
            connection.execute(
                text(
                    "INSERT INTO magic_link_tokens "
                    "(id, account_id, token_hash, expires_at, consumed_at) "
                    "VALUES (:id, :account_id, :token_hash, :expires_at, NULL)"
                ),
                {
                    "id": str(uuid4()),
                    "account_id": account["id"],
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "expires_at": datetime.now(timezone.utc)
                    + timedelta(seconds=ttl_seconds),
                },
            )
            return raw_token
    finally:
        engine.dispose()


def magic_link_is_active(database_url: str, raw_token: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            token = connection.execute(
                text(
                    "SELECT 1 FROM magic_link_tokens "
                    "WHERE token_hash = :token_hash "
                    "AND consumed_at IS NULL AND expires_at > :now"
                ),
                {
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "now": datetime.now(timezone.utc),
                },
            ).first()
            return token is not None
    finally:
        engine.dispose()


def consume_magic_link(
    database_url: str,
    raw_token: str,
    inactivity_seconds: int,
    absolute_seconds: int,
    previous_session: str | None,
) -> tuple[str, str, str] | None:
    now = datetime.now(timezone.utc)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            token = connection.execute(
                text(
                    "SELECT magic_link_tokens.id, accounts.id AS account_id, "
                    "accounts.role FROM magic_link_tokens "
                    "JOIN accounts ON accounts.id = magic_link_tokens.account_id "
                    "WHERE token_hash = :token_hash AND consumed_at IS NULL "
                    "AND expires_at > :now"
                ),
                {
                    "token_hash": sha256(raw_token.encode()).hexdigest(),
                    "now": now,
                },
            ).mappings().first()
            if token is None:
                return None
            consumed = connection.execute(
                text(
                    "UPDATE magic_link_tokens SET consumed_at = :now "
                    "WHERE id = :id AND consumed_at IS NULL"
                ),
                {"id": token["id"], "now": now},
            )
            if consumed.rowcount != 1:
                return None

            if previous_session is not None:
                connection.execute(
                    text(
                        "UPDATE authentication_sessions SET revoked_at = :now "
                        "WHERE session_hash = :session_hash AND revoked_at IS NULL"
                    ),
                    {
                        "now": now,
                        "session_hash": sha256(previous_session.encode()).hexdigest(),
                    },
                )

            raw_session = secrets.token_urlsafe(32)
            raw_csrf = secrets.token_urlsafe(32)
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
                    "account_id": token["account_id"],
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                    "csrf_hash": sha256(raw_csrf.encode()).hexdigest(),
                    "inactive_expires_at": now + timedelta(seconds=inactivity_seconds),
                    "absolute_expires_at": now + timedelta(seconds=absolute_seconds),
                },
            )
            return raw_session, raw_csrf, token["role"]
    finally:
        engine.dispose()


def active_session(
    database_url: str, raw_session: str, inactivity_seconds: int
) -> str | None:
    now = datetime.now(timezone.utc)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            session = connection.execute(
                text(
                    "SELECT authentication_sessions.id, accounts.role, "
                    "authentication_sessions.absolute_expires_at "
                    "FROM authentication_sessions JOIN accounts "
                    "ON accounts.id = authentication_sessions.account_id "
                    "WHERE session_hash = :session_hash AND revoked_at IS NULL "
                    "AND inactive_expires_at > :now AND absolute_expires_at > :now"
                ),
                {
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                    "now": now,
                },
            ).mappings().first()
            if session is None:
                return None
            absolute_expires_at = session["absolute_expires_at"]
            if isinstance(absolute_expires_at, str):
                absolute_expires_at = datetime.fromisoformat(absolute_expires_at)
            refreshed_inactivity = min(
                now + timedelta(seconds=inactivity_seconds), absolute_expires_at
            )
            connection.execute(
                text(
                    "UPDATE authentication_sessions "
                    "SET inactive_expires_at = :inactive_expires_at WHERE id = :id"
                ),
                {"inactive_expires_at": refreshed_inactivity, "id": session["id"]},
            )
            return session["role"]
    finally:
        engine.dispose()


def student_session_details(
    database_url: str, raw_session: str
) -> dict[str, str] | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            student = connection.execute(
                text(
                    "SELECT accounts.role, accounts.email, accounts.display_name "
                    "FROM authentication_sessions JOIN accounts "
                    "ON accounts.id = authentication_sessions.account_id "
                    "WHERE authentication_sessions.session_hash = :session_hash "
                    "AND authentication_sessions.revoked_at IS NULL "
                    "AND authentication_sessions.inactive_expires_at > :now "
                    "AND authentication_sessions.absolute_expires_at > :now "
                    "AND accounts.role = 'student'"
                ),
                {
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                    "now": datetime.now(timezone.utc),
                },
            ).mappings().first()
            return dict(student) if student is not None else None
    finally:
        engine.dispose()


def revoke_session(database_url: str, raw_session: str, raw_csrf: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            revoked = connection.execute(
                text(
                    "UPDATE authentication_sessions SET revoked_at = :now "
                    "WHERE session_hash = :session_hash AND csrf_hash = :csrf_hash "
                    "AND revoked_at IS NULL AND inactive_expires_at > :now "
                    "AND absolute_expires_at > :now"
                ),
                {
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                    "csrf_hash": sha256(raw_csrf.encode()).hexdigest(),
                    "now": datetime.now(timezone.utc),
                },
            )
            return revoked.rowcount == 1
    finally:
        engine.dispose()


def session_authorizes_mutation(
    database_url: str, raw_session: str, raw_csrf: str, role: str
) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            authorized = connection.execute(
                text(
                    "SELECT 1 FROM authentication_sessions JOIN accounts "
                    "ON accounts.id = authentication_sessions.account_id "
                    "WHERE session_hash = :session_hash AND csrf_hash = :csrf_hash "
                    "AND accounts.role = :role AND revoked_at IS NULL "
                    "AND inactive_expires_at > :now AND absolute_expires_at > :now"
                ),
                {
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                    "csrf_hash": sha256(raw_csrf.encode()).hexdigest(),
                    "role": role,
                    "now": datetime.now(timezone.utc),
                },
            ).first()
            return authorized is not None
    finally:
        engine.dispose()
