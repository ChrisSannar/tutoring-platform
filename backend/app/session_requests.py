from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import create_engine, text


def create_session_request(
    database_url: str,
    raw_session: str,
    idempotency_key: str,
    service: str,
    preferred_start: datetime,
    timezone_name: str,
    message: str | None,
) -> dict[str, str | datetime | None]:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            student = connection.execute(
                text(
                    "SELECT accounts.id FROM authentication_sessions "
                    "JOIN accounts ON accounts.id = authentication_sessions.account_id "
                    "WHERE authentication_sessions.session_hash = :session_hash "
                    "AND accounts.role = 'student'"
                ),
                {"session_hash": sha256(raw_session.encode()).hexdigest()},
            ).mappings().one()
            existing = connection.execute(
                text(
                    "SELECT id, student_account_id, idempotency_key, service, "
                    "preferred_start, timezone, message, status "
                    "FROM session_requests WHERE student_account_id = :student_id "
                    "AND idempotency_key = :idempotency_key"
                ),
                {
                    "student_id": student["id"],
                    "idempotency_key": idempotency_key,
                },
            ).mappings().first()
            if existing is not None:
                return dict(existing)
            session_request = {
                "id": str(uuid4()),
                "student_account_id": student["id"],
                "idempotency_key": idempotency_key,
                "service": service,
                "preferred_start": preferred_start.astimezone(timezone.utc),
                "timezone": timezone_name,
                "message": message,
                "status": "pending",
            }
            connection.execute(
                text(
                    "INSERT INTO session_requests "
                    "(id, student_account_id, idempotency_key, service, "
                    "preferred_start, timezone, message, status) VALUES "
                    "(:id, :student_account_id, :idempotency_key, :service, "
                    ":preferred_start, :timezone, :message, :status)"
                ),
                session_request,
            )
            return session_request
    finally:
        engine.dispose()
