from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import create_engine, text

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
