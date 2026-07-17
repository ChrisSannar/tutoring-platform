from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import create_engine, text


def create_inquiry(
    database_url: str,
    email: str,
    message: str,
    client_ip: str,
    hourly_limit: int,
) -> bool:
    now = datetime.now(timezone.utc)
    ip_hash = sha256(client_ip.encode()).hexdigest()
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            recent_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM inquiries "
                    "WHERE submitted_ip_hash = :ip_hash AND created_at >= :window_start"
                ),
                {"ip_hash": ip_hash, "window_start": now - timedelta(hours=1)},
            ).scalar_one()
            if recent_count >= hourly_limit:
                return False
            connection.execute(
                text(
                    "INSERT INTO inquiries "
                    "(id, email, message, status, submitted_ip_hash, created_at) "
                    "VALUES (:id, :email, :message, 'new', :ip_hash, :created_at)"
                ),
                {
                    "id": str(uuid4()),
                    "email": email,
                    "message": message,
                    "ip_hash": ip_hash,
                    "created_at": now,
                },
            )
            return True
    finally:
        engine.dispose()


def archive_inquiry(database_url: str, inquiry_id: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text(
                    "UPDATE inquiries SET status = 'archived' "
                    "WHERE id = :id AND status IN ('new', 'invited')"
                ),
                {"id": inquiry_id},
            )
            return result.rowcount == 1
    finally:
        engine.dispose()


def delete_inquiry(database_url: str, inquiry_id: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("DELETE FROM inquiries WHERE id = :id"), {"id": inquiry_id}
            )
            return result.rowcount == 1
    finally:
        engine.dispose()
