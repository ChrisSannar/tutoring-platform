from sqlalchemy import create_engine, text


def tutor_calendar(database_url: str) -> list[dict]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(
                "SELECT bookings.id, start_at, end_at, funding_kind, focus, meeting_details_snapshot, "
                "price_cents_snapshot, currency_snapshot, status, tutor_timezone, accounts.id AS student_id, "
                "accounts.display_name, accounts.email FROM bookings JOIN accounts ON accounts.id = "
                "student_account_id JOIN tutor_settings ON tutor_settings.id = 1 ORDER BY start_at"
            )).mappings()
            return [{"id": row["id"], "start_at": row["start_at"], "end_at": row["end_at"],
                     "duration_minutes": 60, "tutor_timezone": row["tutor_timezone"],
                     "funding_kind": row["funding_kind"], "focus": row["focus"],
                     "meeting_details": row["meeting_details_snapshot"], "price_cents": row["price_cents_snapshot"],
                     "currency": row["currency_snapshot"], "status": row["status"],
                     "student": {"id": row["student_id"], "display_name": row["display_name"], "email": row["email"]}}
                    for row in rows]
    finally:
        engine.dispose()
