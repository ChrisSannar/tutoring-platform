from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, text

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
                    "accounts.role FROM magic_link_tokens JOIN accounts "
                    "ON accounts.id = magic_link_tokens.account_id "
                    "WHERE token_hash = :token_hash AND consumed_at IS NULL "
                    "AND expires_at > :now"
                ),
                {"token_hash": sha256(raw_token.encode()).hexdigest(), "now": now},
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
            raw_session, raw_csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            connection.execute(
                text(
                    "INSERT INTO authentication_sessions "
                    "(id, account_id, session_hash, csrf_hash, inactive_expires_at, "
                    "absolute_expires_at, revoked_at) VALUES (:id, :account_id, "
                    ":session_hash, :csrf_hash, :inactive, :absolute, NULL)"
                ),
                {
                    "id": str(uuid4()),
                    "account_id": token["account_id"],
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                    "csrf_hash": sha256(raw_csrf.encode()).hexdigest(),
                    "inactive": now + timedelta(seconds=inactivity_seconds),
                    "absolute": now + timedelta(seconds=absolute_seconds),
                },
            )
            return raw_session, raw_csrf, token["role"]
    finally:
        engine.dispose()
