from hashlib import sha256

from sqlalchemy import create_engine, text


def upcoming_booking(database_url: str, raw_session: str) -> dict | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            row = connection.execute(text(
                "SELECT bookings.id, start_at, end_at, funding_kind, focus, meeting_details_snapshot, "
                "price_cents_snapshot, currency_snapshot, status, tutor_timezone FROM bookings "
                "JOIN authentication_sessions ON authentication_sessions.account_id = bookings.student_account_id "
                "JOIN tutor_settings ON tutor_settings.id = 1 WHERE session_hash = :hash AND status = 'upcoming'"
            ), {"hash": sha256(raw_session.encode()).hexdigest()}).mappings().first()
            if row is None: return None
            return {"id": row["id"], "start_at": row["start_at"], "end_at": row["end_at"], "duration_minutes": 60,
                    "tutor_timezone": row["tutor_timezone"], "funding_kind": row["funding_kind"], "focus": row["focus"],
                    "meeting_details": row["meeting_details_snapshot"], "price_cents": row["price_cents_snapshot"],
                    "currency": row["currency_snapshot"], "status": row["status"]}
    finally:
        engine.dispose()
