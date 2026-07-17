from datetime import datetime
from hashlib import sha256

from sqlalchemy import create_engine, text

def get_session_request(
    database_url: str, raw_session: str, session_request_id: str
) -> dict[str, str | datetime | None] | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            session_request = connection.execute(
                text(
                    "SELECT id, service, preferred_start, timezone, message, status "
                    "FROM session_requests WHERE id = :id AND student_account_id = "
                    "(SELECT account_id FROM authentication_sessions "
                    "WHERE session_hash = :session_hash)"
                ),
                {
                    "id": session_request_id,
                    "session_hash": sha256(raw_session.encode()).hexdigest(),
                },
            ).mappings().first()
            return dict(session_request) if session_request is not None else None
    finally:
        engine.dispose()

def list_business_session_requests(database_url: str) -> list[dict[str, object]]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT session_requests.id, session_requests.service, "
                    "session_requests.preferred_start, session_requests.timezone, "
                    "session_requests.message, session_requests.status, "
                    "accounts.id AS student_id, accounts.email AS student_email, "
                    "accounts.display_name AS student_display_name "
                    "FROM session_requests JOIN accounts ON accounts.id = "
                    "session_requests.student_account_id "
                    "ORDER BY session_requests.preferred_start, session_requests.id"
                )
            ).mappings()
            return [
                {
                    "id": row["id"],
                    "service": row["service"],
                    "preferred_start": row["preferred_start"],
                    "timezone": row["timezone"],
                    "message": row["message"],
                    "status": row["status"],
                    "student": {
                        "id": row["student_id"],
                        "email": row["student_email"],
                        "display_name": row["student_display_name"],
                    },
                }
                for row in rows
            ]
    finally:
        engine.dispose()
