from datetime import datetime, timedelta, timezone
from hashlib import sha256

from sqlalchemy import create_engine, text

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
                {"session_hash": sha256(raw_session.encode()).hexdigest(), "now": now},
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
