from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import create_engine, text

def accept_magic_link_request(
    database_url: str,
    email: str,
    ip_address: str,
    email_hourly_limit: int,
    ip_hourly_limit: int,
) -> bool:
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
            if (counts["email_count"] or 0) >= email_hourly_limit or (
                counts["ip_count"] or 0
            ) >= ip_hourly_limit:
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
