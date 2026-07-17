from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import create_engine, text

from app.checkout.creation import response


def aware(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def checkout_status(database_url: str, raw_session: str, provider_id: str, now: datetime) -> dict | None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            row = connection.execute(text(
                "SELECT checkout_sessions.* FROM checkout_sessions JOIN authentication_sessions ON "
                "authentication_sessions.account_id = student_account_id WHERE provider_session_id = :provider "
                "AND session_hash = :hash"
            ), {"provider": provider_id, "hash": sha256(raw_session.encode()).hexdigest()}).mappings().first()
            if row is None: return None
            if row["status"] == "pending" and aware(row["expires_at"]) <= now:
                connection.execute(text("UPDATE checkout_sessions SET status = 'expired' WHERE id = :id"), {"id": row["id"]})
                connection.execute(text("DELETE FROM slot_holds WHERE id = :id"), {"id": row["slot_hold_id"]})
                row = {**dict(row), "status": "expired"}
            return response(row)
    finally:
        engine.dispose()
